import os
import sqlite3
import pandas as pd
import requests as _requests
from typing import Optional

# ─── Azure Maps Tool ────────────────────────────────────────────────────────
class AzureMapsTools:
    BASE_URL    = "https://atlas.microsoft.com/search/fuzzy/json"
    API_VERSION = "1.0"

    def __init__(self):
        self.session = _requests.Session()

    def _make_request(self, params: dict) -> dict:
        api_key = os.getenv("AZURE_MAPS_KEY")
        if not api_key:
            raise ValueError("AZURE_MAPS_KEY not set.")
        params.update({"api-version": self.API_VERSION, "subscription-key": api_key})
        resp = self.session.get(self.BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _get_coordinates(self, society_name: str) -> Optional[tuple]:
        q = (
            society_name
            if "Greater Noida" in society_name
            else f"{society_name}, Greater Noida"
        )
        data = self._make_request({"query": q, "countrySet": "IN", "limit": 1})
        results = data.get("results")
        if not results:
            return None
        pos = results[0]["position"]
        return pos["lat"], pos["lon"]

    def find_nearby_amenity(self, society_name: str, amenity_type: str, radius: int = 5000, limit: int = 10) -> str:
        """Find nearby amenities (schools, hospitals, malls, etc.) near a society."""
        try:
            coords = self._get_coordinates(society_name)
            if not coords:
                return f"Location not found for '{society_name}'."
            lat, lon = coords
            data = self._make_request(
                {"query": amenity_type, "lat": lat, "lon": lon, "radius": radius, "limit": limit}
            )
            results = data.get("results", [])
            if not results:
                return f"No {amenity_type} found within {radius}m of {society_name}."
            filtered = [
                f"- {item.get('poi', {}).get('name', 'Unknown')} ({int(item.get('dist', 0))}m)"
                for item in results
                if "Sector" not in item.get("poi", {}).get("name", "")
            ]
            return f"Nearby {amenity_type}s near '{society_name}':\n" + "\n".join(filtered)
        except _requests.RequestException as e:
            return f"API request failed: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"


# ─── Market Analysis Tool ───────────────────────────────────────────────────
class MarketAnalysisTools:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_market_context(self, locality: str):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(
            f"SELECT rent, area_sqft FROM nobroker_cleaned WHERE Locality = '{locality}'",
            conn,
        )
        conn.close()
        if df.empty:
            return None
        df["price_per_sqft"] = df["rent"] / df["area_sqft"]
        return {
            "locality": locality,
            "median_rent_per_sqft": df["price_per_sqft"].median(),
            "sample_size": len(df),
        }

    def evaluate_deal(self, rent: int, area_sqft: int, locality: str) -> str:
        """Evaluate whether a property deal is fair, overpriced, or a bargain."""
        market_data = self.get_market_context(locality)
        if not market_data:
            return f"No market data available for {locality}."
        prop_ppsf   = rent / area_sqft
        market_med  = market_data["median_rent_per_sqft"]
        diff        = ((prop_ppsf - market_med) / market_med) * 100
        fair_rent   = market_med * area_sqft

        def to_k(amount):
            return f"₹{amount/1000:.1f}k".replace(".0k", "k")

        rl, rh = to_k(fair_rent * 0.95), to_k(fair_rent * 1.02)
        ask_k  = to_k(rent)
        
        if diff > 5.0:
            return f"Property is {diff:.1f}% overpriced vs locality median. Recommended negotiation range {rl}–{rh}."
        elif diff < -5.0:
            return f"Property is {abs(diff):.1f}% underpriced vs locality median. Excellent deal! Recommend locking in near the asking price of {ask_k}."
        else:
            return f"Property is priced at Fair Market Value ({abs(diff):.1f}% variance vs median). Recommended negotiation range {rl}–{rh}."