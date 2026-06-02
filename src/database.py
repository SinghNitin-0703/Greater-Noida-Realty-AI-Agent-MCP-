import os
import sqlite3
import pandas as pd
import re
from config import CSV_PATH, DB_PATH  # Importing paths from our new config module

def build_db_if_needed():
    """Load CSV, clean it, extract localities, and save to SQLite."""
    
    # Check if table already exists
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nobroker_cleaned'")
        if cursor.fetchone():
            print(f"[DB] ✅ Table 'nobroker_cleaned' already exists at {DB_PATH}. Skipping rebuild.")
            conn.close()
            return
        else:
            print(f"[DB] ⚠️ DB exists but table missing. Building from CSV...")
            conn.close()
    else:
        print(f"[DB] DB not found at '{DB_PATH}'. Building from CSV...")

    # Build process
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"\n[DB ERROR] CSV not found at '{CSV_PATH}'. "
            "Please ensure the file exists or update your .env file."
        )

    print(f"[DB] Building database from {CSV_PATH} …")
    df = pd.read_csv(CSV_PATH)

    # --- Clean rent column ---
    df["rent"] = (
        df["rent"].astype(str)
          .str.replace(r"[^\d]", "", regex=True)
          .pipe(pd.to_numeric, errors="coerce")
    )
    df.dropna(subset=["rent", "area_sqft", "apartment_type"], inplace=True)
    df["rent"]      = df["rent"].astype(int)
    df["area_sqft"] = df["area_sqft"].astype(int)

    # Extract numeric BHK
    df["apartment_type"] = (
        df["apartment_type"].astype(str)
          .str.extract(r"(\d+)")[0]
          .pipe(pd.to_numeric, errors="coerce")
    )

    # --- Locality extraction ---
    extraction_patterns = [
        r"Sector\s?\d+[A-Za-z]?", r"Gaur City\s?\d*", r"Noida Extension", 
        r"Greater Noida West", r"Tech Zone\s?[IVX]*", r"Knowledge Park\s?[IVX]*", 
        r"Ecotech\s?[IVX]*", r"Surajpur", r"\bOmicron\s?[IVX]*\b", 
        r"\bDelta\s?[IVX]*\b", r"\bAlpha\s?[IVX]*\b", r"\bBeta\s?[IVX]*\b", 
        r"\bGamma\s?[IVX]*\b", r"\bZeta\s?[IVX]*\b", r"\bEta\s?[IVX]*\b", 
        r"\bMu\s?[IVX]*\b", r"\bChi\s?[IVX]*\b", r"\bPi\s?[IVX]*\b", 
        r"\bOmega\s?[IVX]*\b", r"\bPhi\s?[IVX]*\b", r"\bSigma\s?[IVX]*\b", 
        r"\bRho\b", r"\bTheta\b", r"\bIota\b", r"\bKappa\b", r"\bLambda\b", 
        r"\bNu\b", r"\bXi\b", r"\bTau\b", r"\bUpsilon\b", r"\bPsi\b", r"Greater Noida",
    ]

    def extract_locality(title):
        if not isinstance(title, str): return None
        for pattern in extraction_patterns:
            m = re.search(pattern, title, re.IGNORECASE)
            if m: return m.group(0).strip()
        return None

    df["Locality"] = df["full_title"].apply(extract_locality)
    
    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("nobroker_cleaned", conn, if_exists="replace", index=False)
    conn.close()
    print(f"[DB] ✅ Saved {len(df)} rows to {DB_PATH}")

# Optional: Allow running this file directly to test the DB build
if __name__ == "__main__":
    build_db_if_needed()