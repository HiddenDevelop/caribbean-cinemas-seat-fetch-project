#!/usr/bin/env python3
"""
Fetch available seats for Spider-Man: Brand New Day at Caribbean Cinemas
Plaza Las Américas (San Juan, PR) for August 2, 2026.

Organized by screening time.
Uses the public GraphQL API of the Indy Systems ticketing platform.
"""

import json
import requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Optional

# Configuration
GRAPHQL_URL = "https://home.caribbeancinemas.com/graphql"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Origin": "https://home.caribbeancinemas.com",
    "Accept": "application/json",
    "Referer": "https://home.caribbeancinemas.com/plaza-americas/",
}

# Known showing IDs for Spider-Man: Brand New Day on/near Aug 2, 2026
# (discovered via the site; some earlier IDs become null once past)
AUG2_SHOWING_IDS = [
    906216,  # ~1:10 PM AST
    906217,  # ~1:55 PM AST
    906219,  # ~4:45 PM AST
    906220,  # ~5:30 PM AST
    906222,  # ~8:20 PM AST
    906223,  # ~9:05 PM AST
]

# AST is UTC-4
AST = timezone(timedelta(hours=-4))


def graphql(query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
    payload = {
        "query": query,
        "variables": variables or {},
        "extensions": {
            "clientLibrary": {"name": "@apollo/client", "version": "4.0.9"}
        },
    }
    resp = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        # Return empty on permission / not-found style errors
        return {}
    return data.get("data") or {}


def get_showing(showing_id: int) -> Optional[Dict[str, Any]]:
    query = """
    query ($showingId: ID!) {
      showing(id: $showingId) {
        id
        time
        past
        current
        screen {
          id
          name
          number
        }
        movie {
          id
          name
        }
      }
    }
    """
    data = graphql(query, {"showingId": str(showing_id)})
    return data.get("showing")


def get_seat_chart(showing_id: int) -> Optional[Dict[str, Any]]:
    query = """
    query ($showingId: ID!, $orderId: ID) {
      seatChartForShowing(showingId: $showingId, orderId: $orderId) {
        id
        name
        displayOrder
        seatCount
        seatChartOptions
        seatChart
        __typename
      }
    }
    """
    data = graphql(query, {"showingId": str(showing_id), "orderId": None})
    return data.get("seatChartForShowing")


def parse_available_seats(seat_chart_str: str) -> List[str]:
    """Return list of available seat names (e.g. ['A1', 'A2', ...])."""
    try:
        chart = json.loads(seat_chart_str)
    except (json.JSONDecodeError, TypeError):
        return []

    available = []
    for row in chart:
        for seat in row:
            # Skip aisles / non-seats
            if seat.get("seatType") in ("aisle", None):
                continue
            # Primary availability flag used by the frontend
            if seat.get("available") is True:
                name = seat.get("name")
                if name:
                    available.append(name)
    # Sort naturally: by letter then number
    def seat_key(s: str):
        letter = "".join(c for c in s if c.isalpha()) or "Z"
        num = int("".join(c for c in s if c.isdigit()) or 0)
        return (letter, num)

    return sorted(set(available), key=seat_key)


def format_local_time(iso_utc: str) -> str:
    """Convert ISO UTC string to a friendly AST string."""
    dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    local = dt.astimezone(AST)
    return local.strftime("%I:%M %p").lstrip("0")  # e.g. 1:10 PM


def main():
    print("=" * 70)
    print("Spider-Man: Brand New Day — Available Seats")
    print("Caribbean Cinemas · Plaza Las Américas · August 2, 2026")
    print("=" * 70)
    print()

    results = []

    for sid in AUG2_SHOWING_IDS:
        showing = get_showing(sid)
        if not showing:
            continue
        if showing.get("past"):
            # Skip finished shows
            continue

        movie_name = showing.get("movie", {}).get("name", "Unknown")
        if "Spider-Man" not in movie_name:
            continue

        time_str = format_local_time(showing["time"])
        screen = showing.get("screen", {}).get("name", "Unknown screen")
        is_current = showing.get("current", False)

        chart_data = get_seat_chart(sid)
        if not chart_data:
            available = []
            seat_count = 0
        else:
            available = parse_available_seats(chart_data.get("seatChart", "[]"))
            seat_count = chart_data.get("seatCount") or 0

        results.append(
            {
                "showing_id": sid,
                "time": time_str,
                "time_utc": showing["time"],
                "screen": screen,
                "current": is_current,
                "available_seats": available,
                "available_count": len(available),
                "total_seats": seat_count,
            }
        )

    # Sort by actual UTC time
    results.sort(key=lambda r: r["time_utc"])

    if not results:
        print("No active showtimes found for August 2, 2026.")
        print("The movie may have limited remaining screenings today,")
        print("or the IDs may need updating (check the theater website).")
        return

    for r in results:
        status = " (NOW SHOWING)" if r["current"] else ""
        print(f"▶ {r['time']} AST  ·  {r['screen']}{status}")
        print(f"  Showing ID: {r['showing_id']}")
        print(f"  Available seats: {r['available_count']} / {r['total_seats']}")
        if r["available_seats"]:
            # Print in neat columns
            seats = r["available_seats"]
            for i in range(0, len(seats), 12):
                chunk = seats[i : i + 12]
                print("    " + "  ".join(f"{s:>4}" for s in chunk))
        else:
            print("    (no seats available or chart not loaded)")
        print()

    print("-" * 70)
    print(f"Total active screenings found: {len(results)}")
    print("Data fetched live from Caribbean Cinemas / Indy Systems GraphQL API.")
    print("Seat availability changes in real time — re-run for the latest status.")


if __name__ == "__main__":
    main()