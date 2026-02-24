"""
Real Estate MCP Server
======================
Exposes three tool groups via the Model Context Protocol (MCP) over stdio:

  1. find_nearby_amenity  – Azure Maps fuzzy-search POI lookup
  2. evaluate_deal        – Market analysis against SQLite locality median
  3. SQL tools            – list_tables, describe_table, run_sql_query

Run standalone (for testing):
    python mcp_server.py

The Agno agent connects to this server by passing:
    MCPTools(command="python mcp_server.py", cwd="<project_root>")
"""

import os
import sqlite3

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()  # picks up AZURE_MAPS_KEY from .env

mcp = FastMCP(
    name="realestate-tools",
    instructions="Tools for the Greater Noida real-estate broker agent.",
)

# ---------------------------------------------------------------------------
# Configuration (edit these paths if needed)
# ---------------------------------------------------------------------------
DB_PATH = r"D:\personal Projects\Agentic AI\Reaestate Agent 3\Data\Database\nobroker.db"

AZURE_MAPS_BASE_URL = "https://atlas.microsoft.com/search/fuzzy/json"
AZURE_MAPS_API_VERSION = "1.0"


# ===========================================================================
# Tool Group 1 – Azure Maps (Amenity Finder)
# ===========================================================================

def _azure_request(params: dict) -> dict:
    """Internal helper: adds auth and fires a GET request to Azure Maps."""
    api_key = os.getenv("AZURE_MAPS_KEY")
    if not api_key:
        raise ValueError("AZURE_MAPS_KEY not found in environment variables.")

    params.update({
        "api-version": AZURE_MAPS_API_VERSION,
        "subscription-key": api_key,
    })
    response = requests.get(AZURE_MAPS_BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _get_coordinates(society_name: str) -> tuple | None:
    """Resolves a society name to (lat, lon) using Azure Maps fuzzy search."""
    search_query = (
        society_name
        if "Greater Noida" in society_name
        else f"{society_name}, Greater Noida"
    )
    data = _azure_request({"query": search_query, "countrySet": "IN", "limit": 1})
    results = data.get("results")
    if not results:
        return None
    pos = results[0]["position"]
    return pos["lat"], pos["lon"]


@mcp.tool()
def find_nearby_amenity(
    society_name: str,
    amenity_type: str,
    radius: int = 5000,
    limit: int = 10,
) -> str:
    """
    Find nearby points of interest (POIs) around a housing society in Greater Noida.

    Args:
        society_name: The name of the housing society / apartment complex.
        amenity_type: The type of amenity to search for (e.g. "School", "Hospital",
                      "Mall", "Metro Station"). Use singular form.
        radius:       Search radius in metres (default 5000).
        limit:        Maximum number of results to return (default 10).

    Returns:
        A formatted string listing nearby amenities with distances, or an error message.
    """
    try:
        coords = _get_coordinates(society_name)
        if not coords:
            return f"Location not found for '{society_name}'."

        lat, lon = coords
        data = _azure_request({
            "query": amenity_type,
            "lat": lat,
            "lon": lon,
            "radius": radius,
            "limit": limit,
        })

        results = data.get("results", [])
        if not results:
            return f"No {amenity_type} found within {radius}m of {society_name}."

        filtered = [
            f"- {item.get('poi', {}).get('name', 'Unknown')} ({int(item.get('dist', 0))}m)"
            for item in results
            if "Sector" not in item.get("poi", {}).get("name", "")
        ]

        return (
            f"Nearby {amenity_type}s near '{society_name}':\n" + "\n".join(filtered)
        )

    except requests.RequestException as e:
        return f"API request failed: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# ===========================================================================
# Tool Group 2 – Market Analysis (Deal Evaluator)
# ===========================================================================

def _get_market_context(locality: str) -> dict | None:
    """Fetches price-per-sqft stats for a locality from the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        query = f"""
            SELECT rent, area_sqft
            FROM nobroker_cleaned
            WHERE Locality = '{locality}'
        """
        cursor = conn.execute(query)
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return None

    price_per_sqft_values = [r[0] / r[1] for r in rows if r[1] > 0]
    if not price_per_sqft_values:
        return None

    sorted_vals = sorted(price_per_sqft_values)
    n = len(sorted_vals)
    if n % 2 == 1:
        median = sorted_vals[n // 2]
    else:
        median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

    return {
        "locality": locality,
        "median_rent_per_sqft": median,
        "sample_size": n,
    }


@mcp.tool()
def evaluate_deal(rent: int, area_sqft: int, locality: str) -> str:
    """
    Evaluate whether a property's rent is fair compared to the local market median.

    Args:
        rent:       Monthly rent of the property (in ₹).
        area_sqft:  Carpet/built-up area of the property in square feet.
        locality:   The locality / sector name exactly as stored in the database
                    (e.g. "Sector 10", "Chi V", "Omicron I").

    Returns:
        A negotiation advice string describing how the property compares to the
        market median and suggesting a recommended rent range.
    """
    market_data = _get_market_context(locality)

    if not market_data:
        return f"No market data available for {locality} to evaluate this deal."

    prop_price_per_sqft = rent / area_sqft
    market_median = market_data["median_rent_per_sqft"]
    diff = ((prop_price_per_sqft - market_median) / market_median) * 100
    fair_rent = market_median * area_sqft

    def to_k(amount: float) -> str:
        return f"₹{amount / 1000:.1f}k".replace(".0k", "k")

    range_low = to_k(fair_rent * 0.95)
    range_high = to_k(fair_rent * 1.02)
    asking_rent_k = to_k(rent)

    if diff > 5.0:
        return (
            f"Property is {diff:.1f}% overpriced vs locality median. "
            f"Recommended negotiation range {range_low}–{range_high}."
        )
    elif diff < -5.0:
        return (
            f"Property is {abs(diff):.1f}% underpriced vs locality median. "
            f"Excellent deal! Recommend locking it in near the asking price of {asking_rent_k}."
        )
    else:
        return (
            f"Property is priced at Fair Market Value ({abs(diff):.1f}% variance vs median). "
            f"Recommended negotiation range {range_low}–{range_high}."
        )


# ===========================================================================
# Tool Group 3 – SQL Query Tools (replaces agno SQLTools)
# ===========================================================================

@mcp.tool()
def list_tables() -> str:
    """
    List all tables available in the real-estate SQLite database.

    Returns:
        A newline-separated list of table names.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    if not tables:
        return "No tables found in the database."
    return "Tables:\n" + "\n".join(f"- {t}" for t in tables)


@mcp.tool()
def describe_table(table_name: str) -> str:
    """
    Describe the schema (columns, types, constraints) of a table in the database.

    Args:
        table_name: Name of the table to describe (e.g. "nobroker_cleaned").

    Returns:
        A formatted description of the table's columns.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(f"PRAGMA table_info('{table_name}');")
        columns = cursor.fetchall()
    finally:
        conn.close()

    if not columns:
        return f"Table '{table_name}' not found or has no columns."

    lines = [f"Schema for '{table_name}':", "cid | name | type | notnull | default | pk"]
    lines.append("-" * 55)
    for col in columns:
        lines.append(" | ".join(str(c) for c in col))
    return "\n".join(lines)


@mcp.tool()
def run_sql_query(query: str) -> str:
    """
    Execute a read-only SQL SELECT query against the real-estate database.

    IMPORTANT: Only SELECT queries are allowed. Do NOT use INSERT, UPDATE, DELETE, or DROP.
    The main table is `nobroker_cleaned` with columns:
        full_title (TEXT), society_name (TEXT), rent (INTEGER),
        area_sqft (INTEGER), apartment_type (INTEGER – BHK count),
        preferred_tenants (TEXT), link (TEXT), Locality (TEXT).

    Args:
        query: A valid SQLite SELECT statement.

    Returns:
        Query results as a formatted string, or an error message.
    """
    # Safety guard: block any non-SELECT statements
    normalized = query.strip().upper()
    if not normalized.startswith("SELECT"):
        return "Error: Only SELECT queries are permitted."

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
    except sqlite3.Error as e:
        return f"SQL error: {str(e)}"
    finally:
        conn.close()

    if not rows:
        return "Query returned no results."

    # Format as a simple table
    header = " | ".join(col_names)
    separator = "-" * len(header)
    data_rows = [" | ".join(str(cell) for cell in row) for row in rows]
    return "\n".join([header, separator] + data_rows)


# ===========================================================================
# Entry Point
# ===========================================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
