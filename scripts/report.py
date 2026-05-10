import pandas as pd
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sqlalchemy import create_engine, text

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

# ================================================================
# SETUP
# ================================================================

SCRIPTS_DIR  = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent

DB_PATH = PROJECT_ROOT / "patents.db"
if not DB_PATH.exists():
    DB_PATH = SCRIPTS_DIR / "patents.db"

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CSV_DIR     = OUTPUTS_DIR / "csv"
JSON_DIR    = OUTPUTS_DIR / "json"
PLOTS_DIR   = OUTPUTS_DIR / "plots"
PDF_PATH    = OUTPUTS_DIR / "patent_report.pdf"

for d in [CSV_DIR, JSON_DIR, PLOTS_DIR]:
    os.makedirs(d, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}")
print(f"📂 Using database: {DB_PATH}")

# ================================================================
# LOAD DATA
# ================================================================
relationships = pd.read_sql("SELECT * FROM relationships", engine)
inventors     = pd.read_sql("SELECT * FROM inventors",     engine)
companies     = pd.read_sql("SELECT * FROM companies",     engine)
patents       = pd.read_sql("SELECT * FROM patents",       engine)

print(f"   patents:       {len(patents):,} rows")
print(f"   inventors:     {len(inventors):,} rows")
print(f"   companies:     {len(companies):,} rows")
print(f"   relationships: {len(relationships):,} rows")

# ================================================================
# ANALYSIS
# ================================================================

total_patents = patents["patent_id"].nunique()

# --- Top Inventors ---
top_inventors = (
    relationships
    .groupby("inventor_id")["patent_id"].nunique()
    .reset_index(name="patents")
    .merge(inventors[["inventor_id", "name"]], on="inventor_id", how="left")
    [["name", "patents"]]
    .sort_values("patents", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
top_inventors["name"] = top_inventors["name"].fillna("Unknown").astype(str)

# --- Top Companies ---
top_companies = (
    relationships
    .groupby("company_id")["patent_id"].nunique()
    .reset_index(name="patents")
    .merge(companies[["company_id", "name"]], on="company_id", how="left")
    [["name", "patents"]]
    .sort_values("patents", ascending=False)
    .head(10)
    .reset_index(drop=True)
)
top_companies["name"] = top_companies["name"].fillna("Unknown").astype(str)

# --- Country Trends ---
country_data = (
    relationships
    .merge(inventors[["inventor_id", "country"]], on="inventor_id", how="left")
)
country_counts = (
    country_data
    .dropna(subset=["country"])
    .query("country != ''")
    # Filter out UUID-looking values
    [~country_data["country"].str.contains(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-", case=False, regex=True, na=False
    )]
    .groupby("country")["patent_id"].nunique()
    .reset_index(name="patents")
    .sort_values("patents", ascending=False)
    .reset_index(drop=True)
)
total_country_patents = country_counts["patents"].sum()
if total_country_patents > 0:
    country_counts["share"] = (
        country_counts["patents"] / total_country_patents
    ).round(4)
else:
    country_counts["share"] = 0.0

# --- Yearly Trends ---
year_trends = (
    patents.dropna(subset=["year"])
    .astype({"year": int})
    .groupby("year")["patent_id"].nunique()
    .reset_index(name="patents")
    .sort_values("year")
    .reset_index(drop=True)
)

# ================================================================
# A. CONSOLE REPORT
# ================================================================
print("\n================== PATENT REPORT ===================")
print(f"Total Patents: {total_patents:,}")

print("\nTop Inventors:")
for idx, row in top_inventors.iterrows():
    print(f"  {idx + 1}. {row['name']} - {int(row['patents'])}")

print("\nTop Companies:")
for idx, row in top_companies.iterrows():
    print(f"  {idx + 1}. {row['name']} - {int(row['patents'])}")

if len(country_counts) > 0:
    print("\nTop Countries:")
    for idx, row in country_counts.head(5).iterrows():
        print(f"  {idx + 1}. {row['country']} - {int(row['patents'])} patents "
              f"({row['share'] * 100:.1f}%)")
else:
    print("\nTop Countries: No country data available.")

print("\nPatent Trends by Year:")
for _, row in year_trends.iterrows():
    print(f"  {int(row['year'])}: {int(row['patents'])} patents")

print("=====================================================\n")

# ================================================================
# B. CSV EXPORTS
# ================================================================
top_inventors.to_csv(CSV_DIR / "top_inventors.csv",   index=False)
top_companies.to_csv(CSV_DIR / "top_companies.csv",   index=False)
country_counts.to_csv(CSV_DIR / "country_trends.csv", index=False)
year_trends.to_csv(CSV_DIR   / "year_trends.csv",     index=False)
print(f"✅ CSV files saved  →  {CSV_DIR}")

# ================================================================
# C. JSON REPORT  — all values cast to native Python types
# ================================================================
report = {
    "total_patents": int(total_patents),
    "top_inventors": [
        {"name": str(row["name"]), "patents": int(row["patents"])}
        for _, row in top_inventors.iterrows()
    ],
    "top_companies": [
        {"name": str(row["name"]), "patents": int(row["patents"])}
        for _, row in top_companies.iterrows()
    ],
    "top_countries": [
        {
            "country": str(row["country"]),
            "patents": int(row["patents"]),
            "share":   float(row["share"]),
        }
        for _, row in country_counts.head(10).iterrows()
    ],
    "year_trends": {
        int(row["year"]): int(row["patents"])
        for _, row in year_trends.iterrows()
    },
}

with open(JSON_DIR / "report.json", "w") as f:
    json.dump(report, f, indent=4)
print(f"✅ JSON report saved →  {JSON_DIR / 'report.json'}")

# ================================================================
# D. VISUALIZATIONS
# ================================================================

def _bar(df, x_col, y_col, title, path, color="#4C72B0"):
    if df.empty:
        print(f"   ⚠️  Skipping chart (no data): {title}")
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df[x_col], df[y_col], color=color, edgecolor="white")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=14)
    ax.set_ylabel(y_col.replace("_", " ").title())
    plt.xticks(rotation=40, ha="right", fontsize=9)
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            str(int(bar.get_height())),
            ha="center", va="bottom", fontsize=8,
        )
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

_bar(
    top_inventors, "name", "patents",
    "Top 10 Inventors by Patent Count",
    PLOTS_DIR / "top_inventors.png",
    color="#4C72B0",
)

_bar(
    top_companies, "name", "patents",
    "Top 10 Companies by Patent Count",
    PLOTS_DIR / "top_companies.png",
    color="#DD8452",
)

# Yearly trend — line chart
if not year_trends.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(year_trends["year"], year_trends["patents"],
            marker="o", color="#55A868", linewidth=2)
    ax.fill_between(year_trends["year"], year_trends["patents"],
                    alpha=0.15, color="#55A868")
    ax.set_title("Patent Filings by Year", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Patents")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "patent_trends_by_year.png", dpi=150)
    plt.close()

if not country_counts.empty:
    _bar(
        country_counts.head(5), "country", "patents",
        "Top 5 Countries by Patent Count",
        PLOTS_DIR / "top_countries.png",
        color="#C44E52",
    )

print(f"✅ Plots saved       →  {PLOTS_DIR}")

# ================================================================
# E. PDF REPORT
# ================================================================
doc    = SimpleDocTemplate(str(PDF_PATH), pagesize=letter,
                           leftMargin=inch, rightMargin=inch,
                           topMargin=inch, bottomMargin=inch)
styles = getSampleStyleSheet()

heading2  = ParagraphStyle("Heading2Bold", parent=styles["Heading2"],
                            spaceAfter=4, spaceBefore=12)
mono_line = ParagraphStyle("Mono", parent=styles["Normal"],
                            fontName="Courier", fontSize=9, leading=13)

story = []

# Title
story.append(Paragraph("Patent Analytics Report", styles["Title"]))
story.append(Spacer(1, 8))
story.append(Paragraph(
    f"Total Patents Analysed: <b>{total_patents:,}</b>", styles["Normal"]))
story.append(Spacer(1, 16))

# ---- Console-style summary block ----
story.append(Paragraph("Summary (Console Report)", heading2))
lines = [
    "================== PATENT REPORT ===================",
    f"Total Patents: {total_patents:,}",
    "",
    "Top Inventors:",
]
for idx, row in top_inventors.iterrows():
    lines.append(f"  {idx + 1}. {row['name']} - {int(row['patents'])}")
lines += ["", "Top Companies:"]
for idx, row in top_companies.iterrows():
    lines.append(f"  {idx + 1}. {row['name']} - {int(row['patents'])}")
if len(country_counts) > 0:
    lines += ["", "Top Countries:"]
    for idx, row in country_counts.head(5).iterrows():
        lines.append(
            f"  {idx + 1}. {row['country']} - {int(row['patents'])} patents "
            f"({row['share'] * 100:.1f}%)"
        )
else:
    lines += ["", "Top Countries: No country data available."]
lines.append("=====================================================")

for line in lines:
    story.append(Paragraph(line.replace(" ", "&nbsp;"), mono_line))
story.append(Spacer(1, 16))

# ---- Styled data tables ----
def _section_table(title, df, story, heading2, styles):
    if df.empty:
        return
    story.append(Paragraph(title, heading2))
    table_data = [list(df.columns)] + [
        [str(v) for v in row] for row in df.values
    ]
    tbl = Table(table_data, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1,  0), colors.HexColor("#4C72B0")),
        ("TEXTCOLOR",      (0, 0), (-1,  0), colors.white),
        ("FONTNAME",       (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#EEF2FB")]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

_section_table(
    "Top 10 Inventors",
    top_inventors.rename(columns={"name": "Inventor", "patents": "Patents"}),
    story, heading2, styles,
)
_section_table(
    "Top 10 Companies",
    top_companies.rename(columns={"name": "Company", "patents": "Patents"}),
    story, heading2, styles,
)
if not country_counts.empty:
    _section_table(
        "Top Countries",
        country_counts.head(10)[["country", "patents", "share"]].rename(
            columns={"country": "Country", "patents": "Patents", "share": "Share"}
        ),
        story, heading2, styles,
    )

# ---- Charts ----
story.append(Paragraph("Visualisations", heading2))

plot_files = [
    (PLOTS_DIR / "top_inventors.png",         "Top 10 Inventors"),
    (PLOTS_DIR / "top_companies.png",         "Top 10 Companies"),
    (PLOTS_DIR / "top_countries.png",         "Top 5 Countries"),
    (PLOTS_DIR / "patent_trends_by_year.png", "Patent Filings by Year"),
]

for plot_path, caption in plot_files:
    if plot_path.exists():
        story.append(Image(str(plot_path), width=6 * inch, height=3 * inch))
        story.append(Paragraph(f"<i>{caption}</i>", styles["Normal"]))
        story.append(Spacer(1, 12))

doc.build(story)
print(f"✅ PDF report saved  →  {PDF_PATH}")
print("\nAll outputs complete!")