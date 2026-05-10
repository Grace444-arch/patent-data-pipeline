import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

# Paths resolved relative to this script — works from any working directory
BASE       = Path(__file__).resolve().parent.parent  # project root
DATA_CLEAN = BASE / "data" / "clean"
DB_PATH    = BASE / "patents.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

# ================================================================
# SCHEMA — Create tables explicitly before loading data
# ================================================================
schema_sql = """
CREATE TABLE IF NOT EXISTS patents (
    patent_id   TEXT PRIMARY KEY,
    title       TEXT,
    abstract    TEXT,
    filing_date TEXT,
    year        INTEGER
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id TEXT PRIMARY KEY,
    name        TEXT,
    country     TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id  TEXT PRIMARY KEY,
    name        TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    patent_id   TEXT,
    inventor_id TEXT,
    company_id  TEXT,
    FOREIGN KEY (patent_id)   REFERENCES patents(patent_id),
    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id),
    FOREIGN KEY (company_id)  REFERENCES companies(company_id)
);
"""

with engine.connect() as conn:
    for statement in schema_sql.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            conn.execute(text(stmt))
    conn.commit()

print("✅ Schema created")

# ================================================================
# LOAD — Insert cleaned data into tables
# ================================================================
patents       = pd.read_csv(DATA_CLEAN / "clean_patents.csv")
inventors     = pd.read_csv(DATA_CLEAN / "clean_inventors.csv")
companies     = pd.read_csv(DATA_CLEAN / "clean_companies.csv")
relationships = pd.read_csv(DATA_CLEAN / "relationships.csv")

patents.to_sql("patents",             engine, if_exists="replace", index=False)
inventors.to_sql("inventors",         engine, if_exists="replace", index=False)
companies.to_sql("companies",         engine, if_exists="replace", index=False)
relationships.to_sql("relationships", engine, if_exists="replace", index=False)

print("✅ Data loaded")
print(f"   patents:       {len(patents):,} rows")
print(f"   inventors:     {len(inventors):,} rows")
print(f"   companies:     {len(companies):,} rows")
print(f"   relationships: {len(relationships):,} rows")

# ================================================================
# QUERIES — Run and display all 7 required SQL queries
# ================================================================

queries = {

    "Q1: Top Inventors (who has the most patents?)": """
        SELECT i.name, COUNT(r.patent_id) AS total_patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        GROUP BY r.inventor_id
        ORDER BY total_patents DESC
        LIMIT 10
    """,

    "Q2: Top Companies (which companies own the most patents?)": """
        SELECT c.name, COUNT(r.patent_id) AS total_patents
        FROM relationships r
        JOIN companies c ON r.company_id = c.company_id
        GROUP BY r.company_id
        ORDER BY total_patents DESC
        LIMIT 10
    """,

    "Q3: Countries (which countries produce the most patents?)": """
        SELECT i.country, COUNT(DISTINCT r.patent_id) AS total_patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY i.country
        ORDER BY total_patents DESC
        LIMIT 10
    """,

    "Q4: Trends Over Time (patents per year)": """
        SELECT year, COUNT(*) AS total_patents
        FROM patents
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year ASC
    """,

    "Q5: JOIN Query (patents with inventors and companies)": """
        SELECT
            p.patent_id,
            p.title,
            p.filing_date,
            i.name  AS inventor_name,
            i.country,
            c.name  AS company_name
        FROM patents p
        JOIN relationships r ON p.patent_id  = r.patent_id
        JOIN inventors     i ON r.inventor_id = i.inventor_id
        JOIN companies     c ON r.company_id  = c.company_id
        LIMIT 20
    """,

    "Q6: CTE Query (top inventors with their most frequent company)": """
        WITH inventor_patent_counts AS (
            SELECT inventor_id, COUNT(patent_id) AS total_patents
            FROM relationships
            GROUP BY inventor_id
        ),
        inventor_top_company AS (
            SELECT
                inventor_id,
                company_id,
                COUNT(*) AS collab_count,
                RANK() OVER (PARTITION BY inventor_id ORDER BY COUNT(*) DESC) AS co_rank
            FROM relationships
            GROUP BY inventor_id, company_id
        )
        SELECT
            i.name            AS inventor_name,
            ipc.total_patents,
            c.name            AS top_company
        FROM inventor_patent_counts ipc
        JOIN inventors            i   ON ipc.inventor_id  = i.inventor_id
        JOIN inventor_top_company itc ON itc.inventor_id  = ipc.inventor_id AND itc.co_rank = 1
        JOIN companies            c   ON itc.company_id   = c.company_id
        ORDER BY ipc.total_patents DESC
        LIMIT 10
    """,

    "Q7: Ranking Query (rank inventors using window functions)": """
        SELECT
            inventor_name,
            total_patents,
            RANK()       OVER (ORDER BY total_patents DESC) AS rank,
            DENSE_RANK() OVER (ORDER BY total_patents DESC) AS dense_rank,
            NTILE(4)     OVER (ORDER BY total_patents DESC) AS quartile
        FROM (
            SELECT i.name AS inventor_name, COUNT(r.patent_id) AS total_patents
            FROM relationships r
            JOIN inventors i ON r.inventor_id = i.inventor_id
            GROUP BY r.inventor_id
        )
        ORDER BY total_patents DESC
        LIMIT 20
    """,
}

print("\n" + "=" * 60)
print("  SQL QUERY RESULTS")
print("=" * 60)

for title, sql in queries.items():
    print(f"\n--- {title} ---")
    df = pd.read_sql(text(sql), engine)
    print(df.to_string(index=False))

print("\n" + "=" * 60)
print("✅ All queries complete!")