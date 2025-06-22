import os
import socket
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from PySide6.QtCore import QThread, Signal

from PIL import Image
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