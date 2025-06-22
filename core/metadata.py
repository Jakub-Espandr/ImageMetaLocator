import os
import socket
from pathlib import Path
import base64
import io
from datetime import datetime
import math

try:
    import requests
except ImportError:
    requests = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap

from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS, GPSTAGS
import rawpy
import exifread
from geopy.geocoders import Nominatim

class MetadataWorker(QThread):
    """Worker thread for processing metadata to avoid blocking the UI."""
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            metadata = extract_metadata(self.image_path)
            self.finished.emit(metadata)
        except Exception as e:
            self.error.emit(str(e))

class ConnectionTestWorker(QThread):
    """Worker thread for testing internet and service connectivity."""
    finished = Signal(bool, str)

    def run(self):
        if not requests:
            self.finished.emit(False, "Offline (requests library missing)")
            return

        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            services = {
                "Map Service": "https://www.openstreetmap.org",
                "Geocoding": "https://nominatim.openstreetmap.org/",
                "Map Library": "https://unpkg.com/",
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            for name, url in services.items():
                try:
                    response = requests.get(url, timeout=5, headers=headers, stream=True)
                    response.raise_for_status()
                except requests.exceptions.RequestException:
                    self.finished.emit(False, f"Offline: {name} service unreachable")
                    return
            self.finished.emit(True, "Online")
        except socket.error:
            self.finished.emit(False, "Offline: No internet connection")
        except Exception:
            self.finished.emit(False, "Offline: Connectivity check failed")

def get_exif_data(image_path):
    ext = os.path.splitext(image_path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.tif', '.tiff']:
        image = Image.open(image_path)
        exif_data = {}
        info = image._getexif()
        if not info: return {}
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data["GPSInfo"] = gps_data
            else:
                exif_data[decoded] = value
        return exif_data
    elif ext == '.dng':
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        exif_data = {}
        gps_data = {}
        for tag in tags:
            if "GPS" in tag:
                gps_data[tag] = tags[tag]
            elif "EXIF DateTimeOriginal" in tag:
                exif_data["DateTimeOriginal"] = str(tags[tag])
        if gps_data:
            exif_data["GPSInfo"] = gps_data
        return exif_data
    return {}

def dms_to_dd(dms, ref):
    try:
        degrees, minutes, seconds = [float(x) for x in dms]
    except:
        degrees = float(str(dms[0]))
        minutes = float(str(dms[1]))
        seconds = float(str(dms[2]))
    dd = degrees + minutes / 60 + seconds / 3600
    if ref in ['S', 'W']:
        dd *= -1
    return dd

def get_coordinates(exif_data):
    gps_info = exif_data.get("GPSInfo", {})
    if not gps_info: return None, None, None
    if isinstance(gps_info, dict):
        lat = dms_to_dd(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
        lon = dms_to_dd(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
        alt = gps_info.get("GPSAltitude")
        alt_val = float(alt) if alt else None
    else:
        def parse_dms(val):
            return [float(v.num) / float(v.den) for v in val.values]
        lat = dms_to_dd(parse_dms(gps_info["GPS GPSLatitude"]), str(gps_info["GPS GPSLatitudeRef"]))
        lon = dms_to_dd(parse_dms(gps_info["GPS GPSLongitude"]), str(gps_info["GPS GPSLongitudeRef"]))
        alt_val = float(gps_info["GPS GPSAltitude"].values[0].num) / gps_info["GPS GPSAltitude"].values[0].den if "GPS GPSAltitude" in gps_info else None
    return lat, lon, alt_val

def reverse_geocode(lat, lon):
    try:
        geolocator = Nominatim(user_agent="exif_locator")
        location = geolocator.reverse((lat, lon), language='en')
        return location.address if location else "Unknown"
    except Exception:
        return "Geocoding failed"

def extract_metadata(image_path):
    exif = get_exif_data(image_path)
    lat, lon, alt = get_coordinates(exif)
    date = exif.get("DateTimeOriginal", "Unknown")
    address = reverse_geocode(lat, lon) if lat and lon else "No GPS data"
    return {
        'filename': os.path.basename(image_path),
        'coordinates': (lat, lon) if lat and lon else None,
        'address': address,
        'date': date,
        'altitude': alt,
    }

class ExportWorker(QThread):
    """Worker thread for exporting results as a single PDF file."""
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, image_path: str, metadata: dict, map_html: str, export_path: str, map_image=None):
        super().__init__()
        self.image_path = image_path
        self.metadata = metadata
        self.map_html = map_html  # Not used anymore but kept for compatibility
        self.export_path = export_path
        self.map_image = map_image

    def run(self):
        try:
            if not REPORTLAB_AVAILABLE:
                self.error.emit("ReportLab library not available. Please install it with: pip install reportlab")
                return
            
            self.progress.emit(10)
            
            # Create PDF file path
            pdf_path = Path(self.export_path)
            if pdf_path.suffix.lower() != '.pdf':
                pdf_path = pdf_path.with_suffix('.pdf')
            
            self.progress.emit(20)
            
            # Register fccTYPO fonts
            self.register_fcctypo_fonts()
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            story = []
            
            # Get styles with fccTYPO font
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue,
                fontName='fccTYPO-Bold'
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.darkblue,
                fontName='fccTYPO-Bold'
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                fontName='fccTYPO-Regular'
            )
            
            self.progress.emit(30)
            
            # Add title
            story.append(Paragraph("ImageMetaLocator Report", title_style))
            story.append(Spacer(1, 20))
            
            # Add generation timestamp
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 20))
            
            self.progress.emit(40)
            
            # Add image
            if os.path.exists(self.image_path):
                story.append(Paragraph("Original Image", heading_style))
                try:
                    # Load and process image with higher quality
                    img = Image.open(self.image_path)
                    
                    # Calculate target size with higher DPI
                    # Use table width for consistency (2 + 4 = 6 inches)
                    table_width = 6 * inch  # Match the metadata table width
                    max_height = 5 * inch  # Keep reasonable height limit
                    
                    # Calculate aspect ratio to maintain proportions
                    img_aspect = img.width / img.height
                    target_aspect = table_width / max_height
                    
                    if img_aspect > target_aspect:
                        # Image is wider, fit to table width
                        target_width = table_width
                        target_height = table_width / img_aspect
                    else:
                        # Image is taller, fit to height but limit width to table width
                        target_height = max_height
                        target_width = max_height * img_aspect
                        if target_width > table_width:
                            target_width = table_width
                            target_height = table_width / img_aspect
                    
                    # Resize image with high-quality settings
                    # Use LANCZOS resampling for best quality
                    resized_img = img.resize(
                        (int(target_width), int(target_height)), 
                        Image.Resampling.LANCZOS
                    )
                    
                    # Enhance image quality
                    from PIL import ImageEnhance
                    
                    # Slight sharpening for better detail
                    enhancer = ImageEnhance.Sharpness(resized_img)
                    enhanced_img = enhancer.enhance(1.1)
                    
                    # Slight contrast enhancement
                    contrast_enhancer = ImageEnhance.Contrast(enhanced_img)
                    final_img = contrast_enhancer.enhance(1.05)
                    
                    # Save with maximum quality
                    img_buffer = io.BytesIO()
                    final_img.save(img_buffer, format='JPEG', quality=100, optimize=False)
                    img_buffer.seek(0)
                    
                    # Add high-quality image to PDF
                    pdf_img = RLImage(img_buffer, width=target_width, height=target_height)
                    story.append(pdf_img)
                    story.append(Spacer(1, 20))
                    
                    print(f"Original image processed: {img.width}x{img.height} -> {int(target_width)}x{int(target_height)} inches")
                    
                except Exception as e:
                    story.append(Paragraph(f"Error loading image: {str(e)}", normal_style))
                    print(f"Error processing original image: {e}")
            
            self.progress.emit(60)
            
            # Add metadata section
            story.append(Paragraph("Metadata Information", heading_style))
            
            # Create metadata table with fccTYPO font
            metadata_data = []
            if self.metadata.get('filename'):
                metadata_data.append(['File Name', self.metadata['filename']])
            if self.metadata.get('coordinates'):
                lat, lon = self.metadata['coordinates']
                metadata_data.append(['Coordinates (Decimal)', f"{lat:.6f}, {lon:.6f}"])
                # Add WGS 84 format
                lat_deg, lat_min, lat_sec = self.decimal_to_dms(lat)
                lon_deg, lon_min, lon_sec = self.decimal_to_dms(lon)
                lat_hemisphere = "N" if lat >= 0 else "S"
                lon_hemisphere = "E" if lon >= 0 else "W"
                wgs84_format = f"{lat_deg}° {lat_min}' {lat_sec:.2f}\" {lat_hemisphere}, {lon_deg}° {lon_min}' {lon_sec:.2f}\" {lon_hemisphere}"
                metadata_data.append(['Coordinates (WGS 84)', wgs84_format])
            if self.metadata.get('address'):
                address = self.metadata['address']
                # Split address into two lines if it's long
                if len(address) > 40:
                    # Try to split at natural break points in order of preference
                    split_patterns = [
                        ', ',  # Most common address separator
                        '; ',  # Secondary separator
                        ' - ', # Dash separator
                        ' | ', # Pipe separator
                        ' at ', # "at" location indicator
                        ' near ', # "near" location indicator
                        ' between ', # "between" location indicator
                        ' and ', # "and" conjunction
                        ' & ', # Ampersand separator
                    ]
                    
                    split_address = None
                    for pattern in split_patterns:
                        if pattern in address:
                            parts = address.split(pattern, 1)
                            # Check if both parts are reasonable length
                            if len(parts[0]) >= 10 and len(parts[0]) <= 45 and len(parts[1]) >= 5 and len(parts[1]) <= 45:
                                split_address = f"{parts[0]}{pattern}\n{parts[1]}"
                                break
                    
                    if split_address:
                        metadata_data.append(['Address', split_address])
                    else:
                        # If no natural break found, try to split at the middle
                        # Look for the best split point around the middle
                        mid_point = len(address) // 2
                        best_split = mid_point
                        
                        # Look for a space near the middle
                        for i in range(max(0, mid_point - 10), min(len(address), mid_point + 10)):
                            if address[i] == ' ':
                                best_split = i
                                break
                        
                        first_line = address[:best_split].rstrip()
                        second_line = address[best_split:].lstrip()
                        metadata_data.append(['Address', f"{first_line}\n{second_line}"])
                else:
                    metadata_data.append(['Address', address])
            if self.metadata.get('date'):
                metadata_data.append(['Date Taken', self.metadata['date']])
            if self.metadata.get('altitude') is not None:
                metadata_data.append(['Altitude', f"{self.metadata['altitude']:.2f} m"])
            
            if metadata_data:
                metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
                metadata_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'fccTYPO-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 1), (-1, -1), 'fccTYPO-Regular'),
                ]))
                story.append(metadata_table)
            
            self.progress.emit(70)
            
            # Add captured map image
            if self.metadata.get('coordinates'):
                story.append(Spacer(1, 20))
                story.append(Paragraph("Location Map", heading_style))
                
                print(f"Map image received: {self.map_image is not None}")
                if self.map_image:
                    print("Attempting to add captured map image to PDF...")
                    try:
                        # Calculate proper aspect ratio for the map
                        
                        # Load the image to get its dimensions
                        self.map_image.seek(0)
                        pil_image = Image.open(self.map_image)
                        original_width, original_height = pil_image.size
                        
                        # Calculate aspect ratio
                        aspect_ratio = original_width / original_height
                        
                        # Set target width and calculate height to maintain aspect ratio
                        # Use higher DPI for better quality
                        target_width = 6 * inch  # Increased from 5 to 6 inches
                        target_height = target_width / aspect_ratio
                        
                        # Limit height if it gets too large
                        max_height = 5 * inch  # Increased from 4 to 5 inches
                        if target_height > max_height:
                            target_height = max_height
                            target_width = target_height * aspect_ratio
                        
                        print(f"Original size: {original_width}x{original_height}")
                        print(f"Target size: {target_width:.1f}x{target_height:.1f} inches")
                        
                        # Reset buffer position
                        self.map_image.seek(0)
                        
                        # Add captured map image to PDF with proper aspect ratio and high quality
                        map_img = RLImage(self.map_image, width=target_width, height=target_height)
                        story.append(map_img)
                        story.append(Spacer(1, 10))
                        print("Successfully added captured map image to PDF")
                        
                        # Add map coordinates info
                        lat, lon = self.metadata['coordinates']
                        map_info = f"📍 Latitude: {lat:.6f}°\n📍 Longitude: {lon:.6f}°"
                        story.append(Paragraph(map_info, normal_style))
                    except Exception as e:
                        print(f"Error adding map image: {e}")
                        story.append(Paragraph(f"Error adding map image: {str(e)}", normal_style))
                        # Fallback to local map generation
                        print("Falling back to local map generation...")
                        fallback_map = self.create_local_map(self.metadata['coordinates'])
                        if fallback_map:
                            map_img = RLImage(fallback_map, width=5*inch, height=3*inch)
                            story.append(map_img)
                            print("Added fallback map to PDF")
                else:
                    print("No map image received, using fallback...")
                    # Fallback to local map generation
                    fallback_map = self.create_local_map(self.metadata['coordinates'])
                    if fallback_map:
                        map_img = RLImage(fallback_map, width=5*inch, height=3*inch)
                        story.append(map_img)
                        print("Added fallback map to PDF")
                    else:
                        story.append(Paragraph("Map image could not be generated.", normal_style))
                        print("Failed to generate any map")
            
            # Build PDF
            doc.build(story)
            
            self.progress.emit(100)
            self.finished.emit(str(pdf_path))
            
        except Exception as e:
            self.error.emit(str(e))
    
    def register_fcctypo_fonts(self):
        """Register fccTYPO fonts for use in the PDF."""
        try:
            # Get the assets directory path
            assets_dir = Path(__file__).parent.parent / "assets" / "fonts"
            
            # Register fccTYPO-Regular
            regular_font_path = assets_dir / "fccTYPO-Regular.ttf"
            if regular_font_path.exists():
                pdfmetrics.registerFont(TTFont('fccTYPO-Regular', str(regular_font_path)))
                print("Registered fccTYPO-Regular font")
            else:
                print(f"fccTYPO-Regular font not found at {regular_font_path}")
            
            # Register fccTYPO-Bold
            bold_font_path = assets_dir / "fccTYPO-Bold.ttf"
            if bold_font_path.exists():
                pdfmetrics.registerFont(TTFont('fccTYPO-Bold', str(bold_font_path)))
                print("Registered fccTYPO-Bold font")
            else:
                print(f"fccTYPO-Bold font not found at {bold_font_path}")
                
        except Exception as e:
            print(f"Error registering fccTYPO fonts: {e}")
            # Fallback to default fonts if registration fails
    
    def get_static_map_image(self, coordinates):
        """Create a local map representation without external services."""
        try:
            lat, lon = coordinates
            return self.create_local_map(coordinates)
                
        except Exception as e:
            print(f"Error in get_static_map_image: {e}")
            return self.create_text_map(coordinates)
    
    def create_local_map(self, coordinates):
        """Create a local map representation using PIL."""
        try:
            lat, lon = coordinates
            
            # Create a map-like image
            img_width, img_height = 600, 400
            img = Image.new('RGB', (img_width, img_height), color='#f0f8ff')  # Light blue background
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fall back to basic if not available
            try:
                font_large = ImageFont.truetype("arial.ttf", 20)
                font_medium = ImageFont.truetype("arial.ttf", 16)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw map border
            draw.rectangle([10, 10, img_width-10, img_height-10], outline='#333333', width=2)
            
            # Draw title
            title = "Location Map"
            title_bbox = draw.textbbox((0, 0), title, font=font_large)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (img_width - title_width) // 2
            draw.text((title_x, 30), title, fill='#333333', font=font_large)
            
            # Draw coordinate grid (simplified map)
            grid_color = '#cccccc'
            for i in range(1, 10):
                # Vertical lines
                x = 50 + i * 50
                draw.line([(x, 80), (x, 300)], fill=grid_color, width=1)
                # Horizontal lines
                y = 80 + i * 25
                draw.line([(50, y), (500, y)], fill=grid_color, width=1)
            
            # Draw location marker (center of the grid)
            center_x, center_y = 275, 190
            marker_size = 20
            
            # Draw marker circle
            draw.ellipse([center_x-marker_size, center_y-marker_size, 
                         center_x+marker_size, center_y+marker_size], 
                        fill='#ff4444', outline='#cc0000', width=2)
            
            # Draw marker text
            marker_text = "📍"
            marker_bbox = draw.textbbox((0, 0), marker_text, font=font_medium)
            marker_text_width = marker_bbox[2] - marker_bbox[0]
            marker_text_x = center_x - marker_text_width // 2
            marker_text_y = center_y - 8
            draw.text((marker_text_x, marker_text_y), marker_text, fill='white', font=font_medium)
            
            # Draw coordinate information
            coord_y = 320
            draw.text((50, coord_y), f"Latitude:  {lat:.6f}°", fill='#333333', font=font_medium)
            draw.text((50, coord_y + 25), f"Longitude: {lon:.6f}°", fill='#333333', font=font_medium)
            
            # Draw WGS 84 format
            lat_deg, lat_min, lat_sec = self.decimal_to_dms(lat)
            lon_deg, lon_min, lon_sec = self.decimal_to_dms(lon)
            lat_hemisphere = "N" if lat >= 0 else "S"
            lon_hemisphere = "E" if lon >= 0 else "W"
            wgs84_text = f"WGS 84: {lat_deg}° {lat_min}' {lat_sec:.2f}\" {lat_hemisphere}, {lon_deg}° {lon_min}' {lon_sec:.2f}\" {lon_hemisphere}"
            
            # Split WGS 84 text if too long
            if len(wgs84_text) > 60:
                wgs84_part1 = f"WGS 84: {lat_deg}° {lat_min}' {lat_sec:.2f}\" {lat_hemisphere}"
                wgs84_part2 = f"         {lon_deg}° {lon_min}' {lon_sec:.2f}\" {lon_hemisphere}"
                draw.text((50, coord_y + 50), wgs84_part1, fill='#666666', font=font_small)
                draw.text((50, coord_y + 65), wgs84_part2, fill='#666666', font=font_small)
            else:
                draw.text((50, coord_y + 50), wgs84_text, fill='#666666', font=font_small)
            
            # Add note about coordinates
            note_text = "Use these coordinates in any mapping application"
            draw.text((50, coord_y + 85), note_text, fill='#888888', font=font_small)
            
            # Convert to bytes for ReportLab
            map_buffer = io.BytesIO()
            img.save(map_buffer, format='PNG')
            map_buffer.seek(0)
            
            return map_buffer
            
        except Exception as e:
            print(f"Error creating local map: {e}")
            return self.create_text_map(coordinates)
    
    def create_text_map(self, coordinates):
        """Create a simple text-based map representation."""
        try:
            lat, lon = coordinates
            
            # Create a simple ASCII-style map representation
            map_text = f"""
            Location Map (Text Representation)
            =================================
            
            Coordinates: {lat:.6f}, {lon:.6f}
            
            Map View:
            ┌─────────────────────────────────────┐
            │                                     │
            │           📍 LOCATION               │
            │                                     │
            │         (Photo taken here)          │
            │                                     │
            │                                     │
            └─────────────────────────────────────┘
            
            Latitude:  {lat:.6f}°
            Longitude: {lon:.6f}°
            
            Note: Interactive map not available.
            Use coordinates to view location in any mapping application.
            """
            
            # Convert text to image using PIL
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple image with the text
            img_width, img_height = 600, 400
            img = Image.new('RGB', (img_width, img_height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fall back to basic if not available
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Draw the map text
            lines = map_text.strip().split('\n')
            y_position = 20
            for line in lines:
                if line.strip():
                    draw.text((20, y_position), line.strip(), fill='black', font=font)
                    y_position += 20
            
            # Convert to bytes for ReportLab
            map_buffer = io.BytesIO()
            img.save(map_buffer, format='PNG')
            map_buffer.seek(0)
            
            return map_buffer
            
        except Exception as e:
            print(f"Error creating text map: {e}")
            return None
    
    def decimal_to_dms(self, decimal_degrees: float) -> tuple:
        """Convert decimal degrees to degrees, minutes, seconds."""
        # Handle negative values
        is_negative = decimal_degrees < 0
        decimal_degrees = abs(decimal_degrees)
        
        # Extract degrees, minutes, seconds
        degrees = int(decimal_degrees)
        minutes_decimal = (decimal_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        return degrees, minutes, seconds 