#!/usr/bin/env python3
"""
Caribbean Cinemas helper

- Discover movies currently playing (NOW PLAYING only)
- Fetch poster, banner, and description for each movie
"""

import re
import requests
from bs4 import BeautifulSoup, NavigableString
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Shared configuration
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://home.caribbeancinemas.com",
}

GRAPHQL_HEADERS = {
    **HEADERS,
    "Content-Type": "application/json",
}

IMGIX_BASE = "https://indy-systems.imgix.net"

DEFAULT_THEATERS = [
    "plaza-americas",
    "montehiedra",
    "plaza-carolina",
    "plaza-caribe",
    "plaza-del-sol",
    "arecibo",
    "plaza-guaynabo",
    "catalinas",
    "western-plaza",
    "ponce-towne",
]


# ---------------------------------------------------------------------------
# 1. Discover NOW PLAYING movies
# ---------------------------------------------------------------------------

from html import unescape
from bs4 import BeautifulSoup


def clean_description(raw: str | None) -> str | None:
    """
    Turn a synopsis into plain text.
    Strips tags, decodes entities, collapses whitespace.
    Returns None if nothing useful remains.
    """
    if not raw:
        return None

    # If it looks like HTML, parse it; otherwise treat as plain text
    if "<" in raw and ">" in raw:
        text = BeautifulSoup(raw, "html.parser").get_text(separator=" ", strip=True)
    else:
        text = raw

    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    # Guard against pure CSS/JS dumps or empty results
    if len(text) < 20:
        return None
    if text.count("{") > 3 or text.count(";") > 10:  # likely CSS leftovers
        return None

    return text

def scrape_theater_now_playing(theater_slug: str) -> Dict[str, str]:
    """
    Scrape one theater home page and return only NOW PLAYING movies
    as {slug: title}.
    """
    url = f"https://home.caribbeancinemas.com/{theater_slug}/home/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    movies = {}
    current_section = None

    for el in soup.descendants:
        if isinstance(el, NavigableString):
            text = el.strip().upper()
            if text == "NOW PLAYING":
                current_section = "now_playing"
            elif text == "COMING SOON":
                current_section = "coming_soon"
        elif (
            el.name == "a"
            and el.get("href")
            and "/movie/" in el.get("href", "")
            and current_section == "now_playing"
        ):
            title = el.get_text(strip=True)
            href = el["href"]
            match = re.search(r"/movie/([^/?#]+)", href)
            if match and title and len(title) > 1:
                slug = match.group(1)
                movies[slug] = title

    return movies


def _normalize_title(title: str) -> str:
    """Normalize for deduplication (case, whitespace, trailing numbers)."""
    t = title.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*[\(\[]?\d+[\)\]]?$", "", t)
    return t


def get_caribbean_cinemas_movies(
    theater_slugs: Optional[List[str]] = None,
    max_workers: int = 6,
    quiet: bool = False,
) -> List[Dict[str, str]]:
    """
    Return a deduplicated list of movies currently in NOW PLAYING
    across the sampled Caribbean Cinemas locations.

    Each item: {"slug": "...", "title": "...", "url": "..."}
    """
    if theater_slugs is None:
        theater_slugs = DEFAULT_THEATERS

    all_movies: Dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scrape_theater_now_playing, slug): slug
            for slug in theater_slugs
        }
        for future in as_completed(futures):
            theater = futures[future]
            try:
                movies = future.result()
                all_movies.update(movies)
                if not quiet:
                    print(f"  {theater:20} → {len(movies)} now-playing")
            except Exception as e:
                if not quiet:
                    print(f"  {theater:20} → error: {e}")

    seen_titles = set()
    result = []
    for slug, title in sorted(all_movies.items(), key=lambda x: x[1].lower()):
        key = _normalize_title(title)
        if key in seen_titles:
            continue
        seen_titles.add(key)
        result.append(
            {
                "slug": slug,
                "title": title,
                "url": f"https://home.caribbeancinemas.com/movie/{slug}",
            }
        )

    return result


# ---------------------------------------------------------------------------
# 2. Fetch poster, banner, and description
# ---------------------------------------------------------------------------
def get_movie_images(
    slug: str,
    site_id: int = 45,
    poster_width: int = 600,
    banner_width: int = 1200,
) -> Optional[Dict]:
    query = """
    query ($urlSlug: String!, $siteIds: [ID]) {
      findMovieBySlug(urlSlug: $urlSlug, siteIds: $siteIds) {
        id
        name
        urlSlug
        posterImage
        bannerImage
        synopsis
      }
    }
    """

    payload = {
        "query": query,
        "variables": {"urlSlug": slug, "siteIds": [site_id]},
        "extensions": {
            "clientLibrary": {"name": "@apollo/client", "version": "4.0.9"}
        },
    }

    try:
        resp = requests.post(
            "https://home.caribbeancinemas.com/graphql",
            headers=GRAPHQL_HEADERS,
            json=payload,
            timeout=12,
        )
        resp.raise_for_status()
        movie = resp.json().get("data", {}).get("findMovieBySlug")
    except Exception:
        return None

    if not movie:
        return None

    poster_id = movie.get("posterImage")
    banner_id = movie.get("bannerImage")

    result = {
        "title": movie["name"],
        "slug": movie["urlSlug"],
        "id": movie["id"],
        "description": clean_description(movie.get("synopsis")),
        "poster_id": poster_id,
        "banner_id": banner_id,
        "poster": None,
        "banner": None,
    }

    if poster_id:
        result["poster"] = (
            f"{IMGIX_BASE}/{poster_id}?w={poster_width}&auto=format,compress"
        )
    if banner_id:
        result["banner"] = (
            f"{IMGIX_BASE}/{banner_id}?w={banner_width}&auto=format,compress"
        )

    return result

# ---------------------------------------------------------------------------
# 3. Convenience: now-playing list + images + description
# ---------------------------------------------------------------------------

def get_movies_with_images(
    theater_slugs: Optional[List[str]] = None,
    site_id: int = 45,
    max_workers: int = 6,
) -> List[Dict]:
    """
    Fetch current NOW PLAYING movies and attach poster, banner, and description.
    """
    print("Scanning major Caribbean Cinemas locations (NOW PLAYING only)...\n")
    movies = get_caribbean_cinemas_movies(
        theater_slugs, max_workers=max_workers
    )

    print(f"\nEnriching {len(movies)} movies with images & descriptions...\n")
    enriched = []

    for m in movies:
        info = get_movie_images(m["slug"], site_id=site_id)
        if info:
            enriched.append({**m, **info})
        else:
            enriched.append(
                {
                    **m,
                    "description": None,
                    "poster": None,
                    "banner": None,
                }
            )

    return enriched


# ---------------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    movies = get_movies_with_images()
    print(movies);
    print(f"Found {len(movies)} now-playing movies:\n")
    for i, m in enumerate(movies, 1):
        print(f"{i:2}. {m['title']}")
        print(f"    slug        : {m['slug']}")
        if m.get("description"):
            desc = m["description"]
            # Truncate long descriptions for console display
            
            print(f"    description : {desc}")
        if m.get("poster"):
            print(f"    poster      : {m['poster']}")
        if m.get("banner"):
            print(f"    banner      : {m['banner']}")
        print()