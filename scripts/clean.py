import pandas as pd
import os
from pathlib import Path

BASE     = Path(__file__).resolve().parent.parent
DATA_RAW = BASE / "data" / "raw"
DATA_CLN = BASE / "data" / "clean"
os.makedirs(DATA_CLN, exist_ok=True)

NROWS = 100000
# ================================================================
# PATENTS
# ================================================================
patents   = pd.read_csv(DATA_RAW / "g_patent.tsv",          sep="\t", nrows=NROWS)
abstracts = pd.read_csv(DATA_RAW / "g_patent_abstract.tsv", sep="\t", nrows=NROWS)

print("Patent columns:",   patents.columns.tolist())
print("Abstract columns:", abstracts.columns.tolist())

patents = patents.merge(abstracts, on="patent_id", how="left")
patents = patents[["patent_id", "patent_title", "patent_abstract", "patent_date"]].copy()
patents.columns = ["patent_id", "title", "abstract", "filing_date"]
patents["year"] = pd.to_datetime(patents["filing_date"], errors="coerce").dt.year
patents = patents.dropna(subset=["patent_id", "title", "filing_date"])
patents.to_csv(DATA_CLN / "clean_patents.csv", index=False)

known_ids = set(patents["patent_id"].astype(str))
print(f"✅ Patents: {len(patents):,} rows | sample IDs: {list(known_ids)[:3]}")

# ================================================================
# DEBUG — peek at raw files before processing
# ================================================================
print("\n--- DEBUG: inventor file sample ---")
inv_sample = pd.read_csv(DATA_RAW / "g_inventor_disambiguated.tsv", sep="\t", nrows=3, dtype=str)
print("Columns:", inv_sample.columns.tolist())
print(inv_sample.to_string(index=False))

print("\n--- DEBUG: assignee file sample ---")
asg_sample = pd.read_csv(DATA_RAW / "g_assignee_disambiguated.tsv", sep="\t", nrows=3, dtype=str)
print("Columns:", asg_sample.columns.tolist())
print(asg_sample.to_string(index=False))

loc_file = DATA_RAW / "g_location_disambiguated.tsv"
if loc_file.exists():
    print("\n--- DEBUG: location file sample ---")
    loc_sample = pd.read_csv(loc_file, sep="\t", nrows=3, dtype=str)
    print("Columns:", loc_sample.columns.tolist())
    print(loc_sample.to_string(index=False))

# ================================================================
# INVENTORS
# ================================================================
print("\n   Loading inventors...")
inv_chunks = pd.read_csv(DATA_RAW / "g_inventor_disambiguated.tsv", sep="\t",
                         chunksize=100000, dtype=str)
inv_rows = []
for chunk in inv_chunks:
    chunk["patent_id"] = chunk["patent_id"].astype(str).str.strip()
    matched = chunk[chunk["patent_id"].isin(known_ids)]
    if len(matched):
        inv_rows.append(matched)

inventors_raw = pd.concat(inv_rows, ignore_index=True) if inv_rows else pd.DataFrame()
print(f"   Found {len(inventors_raw):,} inventor rows")

if len(inventors_raw) == 0:
    print("❌ No inventor matches — patent IDs differ between files.")
    print(f"   Patents sample:   {list(known_ids)[:5]}")
    inv_peek = pd.read_csv(DATA_RAW / "g_inventor_disambiguated.tsv", sep="\t", nrows=5, dtype=str)
    print(f"   Inventor patent_id sample: {inv_peek['patent_id'].tolist()}")
else:
    # Build name
    first_col = next((c for c in inventors_raw.columns if "first" in c.lower()), None)
    last_col  = next((c for c in inventors_raw.columns if "last"  in c.lower()), None)
    inventors = inventors_raw[["inventor_id"]].copy()
    inventors["name"] = (
        inventors_raw[first_col].fillna("") + " " +
        inventors_raw[last_col].fillna("")
    ).str.strip() if first_col and last_col else "Unknown"
    inventors = inventors.drop_duplicates("inventor_id")

    # Country — look up from location file
    inventors["country"] = ""
    if loc_file.exists() and "location_id" in inventors_raw.columns:
        locs = pd.read_csv(loc_file, sep="\t", dtype=str)
        print("\nLocation columns:", locs.columns.tolist())

        # Find the right column names dynamically
        loc_id_col   = next((c for c in locs.columns if "location_id" in c.lower()), None)
        loc_ctry_col = next(
            (c for c in locs.columns
             if "country" in c.lower() and "location_id" not in c.lower()),
            None
        )

        print(f"   Using location_id col: {loc_id_col}")
        print(f"   Using country col:     {loc_ctry_col}")

        if loc_id_col and loc_ctry_col:
            locs_slim = locs[[loc_id_col, loc_ctry_col]].rename(
                columns={loc_id_col: "location_id", loc_ctry_col: "country"}
            )
            # Drop rows where country is blank or looks like a UUID
            locs_slim = locs_slim[
                locs_slim["country"].notna() &
                (locs_slim["country"].str.strip() != "") &
                (~locs_slim["country"].str.contains(
                    r"^[0-9a-f]{8}-[0-9a-f]{4}-", case=False, regex=True
                ))
            ]
            inv_with_loc = inventors_raw[["inventor_id", "location_id"]].drop_duplicates()
            inv_with_loc = inv_with_loc.merge(locs_slim, on="location_id", how="left")

            # ── FIXED: drop the empty "country" col before merging to avoid _drop/_x collision ──
            inventors = inventors.drop(columns=["country"])
            inventors = inventors.merge(
                inv_with_loc[["inventor_id", "country"]].drop_duplicates("inventor_id"),
                on="inventor_id",
                how="left",
            )
            inventors["country"] = inventors["country"].fillna("")

            print(f"   Country sample: {inventors['country'].value_counts().head(5).to_dict()}")
        else:
            print("   ⚠️  Could not find country column in location file.")
    else:
        if not loc_file.exists():
            print("   ℹ️  Location file not found — country left blank.")

    inventors = inventors[["inventor_id", "name", "country"]]
    inventors.to_csv(DATA_CLN / "clean_inventors.csv", index=False)
    print(f"✅ Inventors: {len(inventors):,} rows")
    print(inventors.head(3).to_string(index=False))

# ================================================================
# COMPANIES
# ================================================================
print("\n   Loading companies...")
asg_chunks = pd.read_csv(DATA_RAW / "g_assignee_disambiguated.tsv", sep="\t",
                         chunksize=100000, dtype=str)
asg_rows = []
for chunk in asg_chunks:
    chunk["patent_id"] = chunk["patent_id"].astype(str).str.strip()
    matched = chunk[chunk["patent_id"].isin(known_ids)]
    if len(matched):
        asg_rows.append(matched)

companies_raw = pd.concat(asg_rows, ignore_index=True) if asg_rows else pd.DataFrame()
print(f"   Found {len(companies_raw):,} assignee rows")

if len(companies_raw) == 0:
    print("❌ No company matches.")
else:
    print("Assignee columns:", companies_raw.columns.tolist())

    # Find org / name columns dynamically
    org_col   = next((c for c in companies_raw.columns if "organization" in c.lower()), None)
    first_col = next((c for c in companies_raw.columns if "first" in c.lower()), None)
    last_col  = next((c for c in companies_raw.columns if "last"  in c.lower()), None)
    id_col    = next((c for c in companies_raw.columns if "assignee_id" in c.lower()), None)

    print(f"   org_col={org_col}, id_col={id_col}")

    companies = companies_raw[[id_col]].copy().rename(columns={id_col: "company_id"})

    if org_col:
        companies["name"] = companies_raw[org_col].astype(str).str.strip()
    else:
        companies["name"] = ""

    # Fallback to individual name where org is blank/NaN/"nan"/"0"
    if first_col and last_col:
        mask = (
            companies["name"].isna() |
            companies["name"].isin(["", "nan", "0", "NaN"]) |
            (companies["name"].str.strip() == "")
        )
        individual = (
            companies_raw[first_col].fillna("") + " " +
            companies_raw[last_col].fillna("")
        ).str.strip()
        companies.loc[mask, "name"] = individual[mask]

    # Drop rows that are still blank or "0"
    companies = companies[
        companies["name"].notna() &
        ~companies["name"].isin(["", "nan", "0", "NaN"]) &
        (companies["name"].str.strip() != "")
    ]
    companies = companies.drop_duplicates("company_id")
    companies.to_csv(DATA_CLN / "clean_companies.csv", index=False)
    print(f"✅ Companies: {len(companies):,} rows")
    print(companies.head(3).to_string(index=False))

# ================================================================
# RELATIONSHIPS
# ================================================================
if inv_rows and asg_rows:
    inv_rel = inventors_raw[["patent_id", "inventor_id"]].copy()
    asg_rel = companies_raw[["patent_id", "assignee_id"]].copy().rename(
        columns={"assignee_id": "company_id"}
    )
    relationships = pd.merge(inv_rel, asg_rel, on="patent_id", how="inner")
    relationships.columns = ["patent_id", "inventor_id", "company_id"]
    relationships = relationships[relationships["patent_id"].isin(known_ids)]
    relationships.to_csv(DATA_CLN / "relationships.csv", index=False)
    print(f"✅ Relationships: {len(relationships):,} rows")
else:
    pd.DataFrame(columns=["patent_id", "inventor_id", "company_id"]).to_csv(
        DATA_CLN / "relationships.csv", index=False)
    print("⚠️  Relationships: 0 rows")

print("\nAll cleaning done!")