# -*- coding: utf-8 -*-
"""
Utility functions: string normalization, geolocation, image/menu matching, encoding.
"""
import os
import base64
import chardet
import difflib
import unicodedata
import pandas as pd
from math import radians, cos, sin, asin, sqrt
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from modules.config import IMAGES_DIR, MENUS_DIR, BAR_MENU_MAPPING


def normalize_string(s):
    """Normalize string for comparison (remove accents, lowercase, etc.)"""
    if not isinstance(s, str):
        return ""
    ns = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return ns.lower().strip().replace(' ', '_').replace('-', '_')


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers.
    return c * r


def get_coordinates(address):
    """Geocode an address to (lat, lon) using Nominatim."""
    geo_locator = Nominatim(user_agent="echec_map_app")
    try:
        location = geo_locator.geocode(address)
        if location:
            return location.latitude, location.longitude
        return None
    except GeocoderTimedOut:
        return None


def find_closest_bar(user_lat, user_lon, df):
    """Find the closest bar to the user's coordinates."""
    min_dist = float('inf')
    closest_bar = None

    for _, row in df.iterrows():
        try:
            bar_lat = float(row['lat'])
            bar_lon = float(row['lon'])
            dist = haversine(user_lon, user_lat, bar_lon, bar_lat)
            if dist < min_dist:
                min_dist = dist
                closest_bar = row['Nom']
        except:
            continue

    return closest_bar, min_dist


def find_best_image_match(bar_name, images_dir=None):
    """Find the best matching image file for a given bar name using fuzzy matching."""
    if images_dir is None:
        images_dir = IMAGES_DIR
    if not os.path.exists(images_dir):
        return None

    normalized_name = normalize_string(bar_name)

    try:
        files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        image_files = [f for f in files if any(f.lower().endswith(ext) for ext in valid_extensions)]
    except Exception:
        return None

    # 1. Exact match (normalized)
    for img_file in image_files:
        if normalize_string(os.path.splitext(img_file)[0]) == normalized_name:
            return os.path.join(images_dir, img_file)

    # 2. Fuzzy match
    norm_map = {normalize_string(os.path.splitext(f)[0]): f for f in image_files}
    matches = difflib.get_close_matches(normalized_name, norm_map.keys(), n=1, cutoff=0.6)

    if matches:
        return os.path.join(images_dir, norm_map[matches[0]])

    return None


def get_menu_pdf_path(bar_name):
    """Find the menu PDF for a given bar with manual mapping and fuzzy logic fallback."""
    if not os.path.exists(MENUS_DIR):
        return None

    # 1. Manual Mapping
    if bar_name in BAR_MENU_MAPPING:
        pdf_path = os.path.join(MENUS_DIR, BAR_MENU_MAPPING[bar_name])
        if os.path.exists(pdf_path):
            return pdf_path

    normalized_name = normalize_string(bar_name)

    # Direct match
    pdf_path = os.path.join(MENUS_DIR, f"{normalized_name}.pdf")
    if os.path.exists(pdf_path):
        return pdf_path

    # Fuzzy logic
    try:
        files = [f for f in os.listdir(MENUS_DIR) if f.lower().endswith('.pdf')]
    except:
        return None

    for f in files:
        if normalize_string(os.path.splitext(f)[0]) == normalized_name:
            return os.path.join(MENUS_DIR, f)

    norm_map = {normalize_string(os.path.splitext(f)[0]): f for f in files}
    matches = difflib.get_close_matches(normalized_name, norm_map.keys(), n=1, cutoff=0.5)
    if matches:
        return os.path.join(MENUS_DIR, norm_map[matches[0]])

    return None


def detect_encoding(file_path):
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result['encoding']


def get_img_as_base64(file_path):
    """Read an image file and return it as a base64 string."""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def extract_arrondissement(code_postal):
    """Extract arrondissement from postal code (75002 -> 2e arr.)"""
    if pd.isna(code_postal):
        return None
    code_str = str(code_postal)
    if code_str.startswith('75') and len(code_str) == 5:
        arr_num = int(code_str[3:])
        return f"{arr_num}e arr."
    return None
