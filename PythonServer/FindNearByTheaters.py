#!/usr/bin/env python3
"""
Find Caribbean Cinemas locations near a ZIP code.
"""

import math
import requests
from typing import List, Dict, Optional

# ---------------------------------------------------------------------------
# Curated list of Puerto Rico locations
# (slug, name, approx latitude, approx longitude, known siteId or None)
# Coordinates are approximate center of the mall/theater.
# ---------------------------------------------------------------------------
THEATERS = [
    # San Juan / Metro area
    {"slug": "plaza-americas",   "name": "Plaza Las Américas",      "lat": 18.4210, "lng": -66.0730, "site_id": 45},
    {"slug": "montehiedra",      "name": "Montehiedra",             "lat": 18.3400, "lng": -66.0800, "site_id": None},
    {"slug": "plaza-carolina",   "name": "Plaza Carolina",          "lat": 18.3930, "lng": -65.9580, "site_id": None},
    {"slug": "plaza-escorial",   "name": "Plaza Escorial",          "lat": 18.3900, "lng": -65.9600, "site_id": None},
    {"slug": "plaza-del-sol",    "name": "Plaza del Sol",           "lat": 18.3980, "lng": -66.1550, "site_id": None},
    {"slug": "plaza-guaynabo",   "name": "Plaza Guaynabo",          "lat": 18.3600, "lng": -66.1120, "site_id": None},
    {"slug": "san-patricio",     "name": "San Patricio VIP",        "lat": 18.4070, "lng": -66.1000, "site_id": None},
    {"slug": "distrito",         "name": "Distrito VIP Cinemas",    "lat": 18.4650, "lng": -66.1050, "site_id": None},
    {"slug": "famiramar",        "name": "Fine Arts Miramar",       "lat": 18.4550, "lng": -66.0800, "site_id": None},
    {"slug": "fapopular",        "name": "Fine Arts Popular",       "lat": 18.4655, "lng": -66.1160, "site_id": None},
    {"slug": "metro",            "name": "Metro Cinemas",           "lat": 18.4300, "lng": -66.0600, "site_id": None},
    {"slug": "rio-hondo",        "name": "Río Hondo 1",             "lat": 18.4200, "lng": -66.1600, "site_id": None},
    {"slug": "rio-hondo-two",    "name": "Río Hondo 2",             "lat": 18.4200, "lng": -66.1600, "site_id": None},

    # North / West
    {"slug": "aguadilla",        "name": "Aguadilla",               "lat": 18.4300, "lng": -67.1500, "site_id": None},
    {"slug": "arecibo",          "name": "Arecibo Cinemas",         "lat": 18.4500, "lng": -66.7300, "site_id": None},
    {"slug": "barceloneta",      "name": "Barceloneta",             "lat": 18.4500, "lng": -66.5400, "site_id": None},
    {"slug": "dorado",           "name": "Dorado",                  "lat": 18.4600, "lng": -66.2800, "site_id": None},
    {"slug": "vega-alta",        "name": "Vega Alta",               "lat": 18.4100, "lng": -66.3400, "site_id": None},
    {"slug": "plaza-del-norte",  "name": "Plaza del Norte",         "lat": 18.4700, "lng": -66.7000, "site_id": None},
    {"slug": "plaza-isabela",    "name": "Plaza Isabela",           "lat": 18.5000, "lng": -67.0200, "site_id": None},
    {"slug": "western-plaza",    "name": "Western Plaza",           "lat": 18.2000, "lng": -67.1400, "site_id": None},
    {"slug": "san-german",       "name": "San Germán",              "lat": 18.0800, "lng": -67.0400, "site_id": None},

    # East
    {"slug": "fajardo",          "name": "Fajardo",                 "lat": 18.3300, "lng": -65.6500, "site_id": None},
    {"slug": "las-piedras",      "name": "Las Piedras",             "lat": 18.1800, "lng": -65.8700, "site_id": None},
    {"slug": "catalinas",        "name": "Las Catalinas (Caguas)",  "lat": 18.2300, "lng": -66.0400, "site_id": None},
    {"slug": "plaza-cayey",      "name": "Plaza Cayey",             "lat": 18.1100, "lng": -66.1600, "site_id": None},

    # South
    {"slug": "plaza-caribe",     "name": "Plaza del Caribe",        "lat": 18.0100, "lng": -66.6100, "site_id": None},
    {"slug": "ponce-towne",      "name": "Ponce Towne",             "lat": 18.0000, "lng": -66.6100, "site_id": None},
    {"slug": "guayama",          "name": "Guayama",                 "lat": 17.9800, "lng": -66.1100, "site_id": None},
    {"slug": "santa-isabel",     "name": "Santa Isabel",            "lat": 17.9700, "lng": -66.4000, "site_id": None},
    {"slug": "belz",             "name": "The Outlet 66",           "lat": 18.2300, "lng": -66.0400, "site_id": None},
]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in miles between two points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geocode_zip(zip_code: str, country: str = "PR") -> Optional[tuple[float, float]]:
    """
    Geocode a ZIP code using OpenStreetMap Nominatim (free, no key required).
    Returns (lat, lng) or None.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "postalcode": zip_code,
        "country": country,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": "CaribbeanCinemasLocator/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


def find_theaters_near_zip(
    zip_code: str,
    radius_miles: float = 15.0,
    country: str = "PR",
) -> List[Dict]:
    """
    Return all theaters within `radius_miles` of the given ZIP code.
    """
    coords = geocode_zip(zip_code, country)
    if not coords:
        raise ValueError(f"Could not geocode ZIP code: {zip_code}")

    origin_lat, origin_lng = coords
    results = []

    for t in THEATERS:
        dist = haversine(origin_lat, origin_lng, t["lat"], t["lng"])
        if dist <= radius_miles:
            results.append({
                "slug": t["slug"],
                "name": t["name"],
                "site_id": t["site_id"],
                "distance_miles": round(dist, 1),
                "lat": t["lat"],
                "lng": t["lng"],
                "url": f"https://home.caribbeancinemas.com/{t['slug']}/home/",
            })

    # Sort by distance
    results.sort(key=lambda x: x["distance_miles"])
    return results


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    zip_code = "00918"          # San Juan (Plaza Las Américas area)
    radius = 12                 # miles

    theaters = find_theaters_near_zip(zip_code, radius_miles=radius)

    print(f"Theaters within {radius} miles of ZIP {zip_code}:\n")
    for t in theaters:
        site = t["site_id"] if t["site_id"] else "unknown"
        print(f"{t['distance_miles']:5.1f} mi  |  {t['name']:30}  slug={t['slug']:20}  siteId={site}")