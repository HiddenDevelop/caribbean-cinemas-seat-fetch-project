import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def get_movies_at_theater(theater_slug: str = "plaza-americas") -> list[dict]:
    """
    Return list of movies currently listed at a Caribbean Cinemas theater.
    
    theater_slug examples:
      - plaza-americas
      - plaza-del-caribe
      - montehiedra
      - etc.
    """
    url = f"https://home.caribbeancinemas.com/{theater_slug}/home/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    movies = []
    seen = set()
    
    for a in soup.find_all("a", href=re.compile(rf"/{theater_slug}/movie/")):
        href = a.get("href", "")
        name = a.get_text(strip=True)
        
        # Extract the movie slug from the URL
        match = re.search(rf"/{theater_slug}/movie/([^/?#]+)", href)
        if not match or not name:
            continue
            
        slug = match.group(1)
        if slug in seen:
            continue
        seen.add(slug)
        
        movies.append({
            "name": name,
            "slug": slug,
            "url": urljoin("https://home.caribbeancinemas.com", href),
        })
    
    return movies


# Example usage
#movies = get_movies_at_theater("plaza-americas")

#print(f"Found {len(movies)} movies:\n")
#for m in movies:
   # print(f"• {m['name']}")
   # print(f"  slug: {m['slug']}")
   # print()