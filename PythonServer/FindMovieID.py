import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Content-Type": "application/json",
    "Origin": "https://home.caribbeancinemas.com",
    "Accept": "application/json",
}

def get_movie_id(slug: str, site_id: int = 45) -> str | None:
    """
    Look up a movie ID by its URL slug.
    site_id 45 = Plaza Las Américas
    """
    query = """
    query ($urlSlug: String!, $siteIds: [ID]) {
      findMovieBySlug(urlSlug: $urlSlug, siteIds: $siteIds) {
        id
        name
        urlSlug
      }
    }
    """
    payload = {
        "query": query,
        "variables": {
            "urlSlug": slug,
            "siteIds": [site_id]
        },
        "extensions": {
            "clientLibrary": {"name": "@apollo/client", "version": "4.0.9"}
        },
    }
    resp = requests.post(
        "https://home.caribbeancinemas.com/graphql",
        headers=HEADERS,
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    movie = resp.json().get("data", {}).get("findMovieBySlug")
    return movie["id"] if movie else None


# Usage
#movie_id = get_movie_id("spider-man-brand-new-day")
#print(movie_id)   # → 486088