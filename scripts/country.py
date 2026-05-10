import pandas as pd
from pathlib import Path

DATA_RAW = Path(r"C:\Users\user\Desktop\patent-data-pipeline\data\raw")

# ── 1. Location file columns + sample ───────────────────────────
print("=" * 60)
print("LOCATION FILE")
print("=" * 60)
loc = pd.read_csv(DATA_RAW / "g_location_disambiguated.tsv",
                  sep="\t", nrows=20, dtype=str)
print("Columns:", loc.columns.tolist())
print(loc.to_string(index=False))

# ── 2. Country column value counts ──────────────────────────────
print("\n" + "=" * 60)
print("COUNTRY COLUMN — top 20 values")
print("=" * 60)
loc_full = pd.read_csv(DATA_RAW / "g_location_disambiguated.tsv",
                       sep="\t", dtype=str)
for col in loc_full.columns:
    if "country" in col.lower():
        print(f"\nColumn: '{col}'")
        vc = loc_full[col].value_counts(dropna=False).head(20)
        print(vc.to_string())

# ── 3. Inventor → location_id presence check ────────────────────
print("\n" + "=" * 60)
print("INVENTOR FILE — columns + sample")
print("=" * 60)
inv = pd.read_csv(DATA_RAW / "g_inventor_disambiguated.tsv",
                  sep="\t", nrows=10, dtype=str)
print("Columns:", inv.columns.tolist())
print(inv.to_string(index=False))

# ── 4. Join test: inventors → locations ─────────────────────────
print("\n" + "=" * 60)
print("JOIN TEST: inventors ↔ locations")
print("=" * 60)
inv_full = pd.read_csv(DATA_RAW / "g_inventor_disambiguated.tsv",
                       sep="\t", nrows=100000, dtype=str)
if "location_id" in inv_full.columns:
    merged = inv_full.merge(loc_full, on="location_id", how="left")
    for col in merged.columns:
        if "country" in col.lower() and col != "location_id":
            non_null = merged[col].notna().sum()
            sample   = merged[col].value_counts(dropna=False).head(10)
            print(f"\nMerged country col '{col}': {non_null} non-null values")
            print(sample.to_string())
else:
    print("⚠️  No 'location_id' column found in inventor file!")
    print("    Inventor columns:", inv_full.columns.tolist())
