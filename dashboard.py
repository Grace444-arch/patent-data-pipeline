"""
Patent Analytics Dashboard — Enhanced with new analyses & beautiful charts
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.patches as mpatches
from scipy.interpolate import make_interp_spline
from sqlalchemy import create_engine, text
from pathlib import Path

# ── NEW IMPORTS for Comparative Map ──────────────────────────────────────────
import plotly.graph_objects as go
import plotly.io as pio

try:
    import pycountry
    _HAS_PYCOUNTRY = True
except ImportError:
    _HAS_PYCOUNTRY = False

# ================================================================
# CONFIG
# ================================================================
st.set_page_config(
    page_title="Patent Analytics Dashboard",
    page_icon="📄",
    layout="wide",
)

# ================================================================
# CUSTOM CSS STYLING
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:           #07090f;
    --bg-card:      #0e1117;
    --bg-hover:     #151923;
    --border:       #1e2433;
    --border-glow:  #2a3450;
    --accent:       #4f8ef7;
    --accent2:      #00d4a0;
    --accent3:      #f5a623;
    --accent4:      #e05c7a;
    --text-1:       #eaf0fb;
    --text-2:       #7b8db0;
    --text-3:       #4a5570;
    --radius:       12px;
    --shadow:       0 8px 32px rgba(0,0,0,.6);
    --glow-blue:    0 0 24px rgba(79,142,247,.18);
    --glow-green:   0 0 24px rgba(0,212,160,.15);
}

html, body, .stApp {
    background-color: var(--bg) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-1) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 2.2rem 2.8rem 5rem !important;
    max-width: 1500px !important;
}

/* -- Sidebar -- */
section[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--text-1) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.85rem !important;
    padding: 0.4rem 0.7rem !important;
    border-radius: 7px !important;
    transition: background 0.15s ease !important;
    letter-spacing: 0.02em !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: var(--bg-hover) !important;
}

/* -- Page headings -- */
h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.95rem !important;
    color: var(--text-1) !important;
    letter-spacing: -0.6px !important;
    margin-bottom: 0.2rem !important;
}
h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-1) !important;
    letter-spacing: -0.3px !important;
}
.stMarkdown p {
    color: var(--text-2) !important;
    font-size: 0.88rem !important;
    line-height: 1.55 !important;
}

/* -- Section label pills -- */
.section-label {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 0.6rem;
}
.label-desc  { background: rgba(79,142,247,.15); color: #4f8ef7; border: 1px solid rgba(79,142,247,.3); }
.label-pred  { background: rgba(0,212,160,.12);  color: #00d4a0; border: 1px solid rgba(0,212,160,.28); }
.label-map   { background: rgba(245,166,35,.12); color: #f5a623; border: 1px solid rgba(245,166,35,.28); }

/* -- Metric cards -- */
div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.3rem 1.6rem !important;
    box-shadow: var(--shadow) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease !important;
}
div[data-testid="metric-container"]:hover {
    border-color: var(--accent) !important;
    box-shadow: var(--glow-blue) !important;
    transform: translateY(-3px) !important;
}
div[data-testid="metric-container"] label {
    color: var(--text-2) !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--text-1) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    color: var(--accent2) !important;
    font-size: 0.76rem !important;
}

/* -- DataFrames -- */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow) !important;
}

/* -- Buttons -- */
.stDownloadButton button, .stButton button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 0.45rem 1.15rem !important;
    border-radius: 7px !important;
    cursor: pointer !important;
    transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease !important;
    letter-spacing: 0.04em !important;
}
.stDownloadButton button:hover, .stButton button:hover {
    background: var(--accent) !important;
    color: #fff !important;
    box-shadow: var(--glow-blue) !important;
}

/* -- Inputs -- */
.stTextInput input, .stMultiSelect > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 7px !important;
    color: var(--text-1) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.875rem !important;
}
.stTextInput input:focus { border-color: var(--accent) !important; }
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(79,142,247,.18) !important;
    color: var(--accent) !important;
    border-radius: 5px !important;
    font-size: 0.78rem !important;
}

div[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border-left-width: 3px !important;
    font-size: 0.84rem !important;
}

hr { border-color: var(--border) !important; margin: 1.8rem 0 !important; }

.stSubheader, [data-testid="stSubheader"] {
    font-size: 1.02rem !important;
    font-weight: 600 !important;
    color: var(--text-1) !important;
    padding-bottom: 0.45rem !important;
    border-bottom: 1px solid var(--border) !important;
    margin-bottom: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)

# ================================================================
# MATPLOTLIB DARK THEME
# ================================================================
BG_CARD   = "#0e1117"
BG_PLOT   = "#0a0d14"
BORDER_C  = "#1e2433"
TEXT_1    = "#eaf0fb"
TEXT_2    = "#7b8db0"
ACCENT    = "#4f8ef7"
ACCENT2   = "#00d4a0"
ACCENT3   = "#f5a623"
ACCENT4   = "#e05c7a"
PALETTE   = [ACCENT, ACCENT3, ACCENT2, ACCENT4, "#b06af7", "#60c9f8", "#ff8c69", "#a3e635"]

PIE_PALETTE = [
    "#4f8ef7", "#00d4a0", "#f5a623", "#e05c7a",
    "#b06af7", "#60c9f8", "#ff8c69", "#a3e635",
    "#f76b8a", "#38bdf8", "#fbbf24", "#34d399",
]

plt.rcParams.update({
    "figure.facecolor":  BG_CARD,
    "axes.facecolor":    BG_PLOT,
    "axes.edgecolor":    BORDER_C,
    "axes.labelcolor":   TEXT_2,
    "axes.titlecolor":   TEXT_1,
    "axes.titlesize":    13,
    "axes.labelsize":    9,
    "axes.grid":         True,
    "grid.color":        "#161c2a",
    "grid.linewidth":    0.5,
    "grid.linestyle":    "--",
    "xtick.color":       TEXT_2,
    "ytick.color":       TEXT_2,
    "xtick.labelsize":   8,
    "ytick.labelsize":   8,
    "text.color":        TEXT_2,
    "legend.facecolor":  "#111827",
    "legend.edgecolor":  BORDER_C,
    "legend.labelcolor": TEXT_1,
    "legend.fontsize":   8,
    "font.family":       "sans-serif",
    "font.size":         9,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.spines.left":  True,
    "axes.spines.bottom":True,
})

# ================================================================
# DB CONNECTION
# ================================================================
@st.cache_resource
def get_engine():
    base = Path(__file__).resolve().parent
    db_path = base / "patents.db"
    if not db_path.exists():
        db_path = base.parent / "patents.db"
    return create_engine(f"sqlite:///{db_path}")

engine = get_engine()

# ================================================================
# DATA LOADERS  (original — zero logic changes)
# ================================================================
@st.cache_data
def load_top_inventors(limit=10):
    sql = """
        SELECT i.name AS inventor, COUNT(r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        GROUP BY r.inventor_id ORDER BY patents DESC LIMIT :limit
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})

@st.cache_data
def load_top_companies(limit=10):
    sql = """
        SELECT c.name AS company, COUNT(r.patent_id) AS patents
        FROM relationships r
        JOIN companies c ON r.company_id = c.company_id
        GROUP BY r.company_id ORDER BY patents DESC LIMIT :limit
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})

@st.cache_data
def load_top_countries(limit=10):
    sql = """
        SELECT i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY i.country ORDER BY patents DESC LIMIT :limit
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})

@st.cache_data
def load_year_trends():
    sql = """
        SELECT year, COUNT(*) AS patents
        FROM patents WHERE year IS NOT NULL
        GROUP BY year ORDER BY year ASC
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_summary():
    sql = """
        SELECT
            (SELECT COUNT(*) FROM patents)       AS total_patents,
            (SELECT COUNT(*) FROM inventors)     AS total_inventors,
            (SELECT COUNT(*) FROM companies)     AS total_companies,
            (SELECT COUNT(*) FROM relationships) AS total_relationships
    """
    return pd.read_sql(text(sql), engine).iloc[0]

@st.cache_data
def load_join_sample(limit=200):
    sql = """
        SELECT p.patent_id, p.title, p.filing_date, p.year,
               i.name AS inventor, i.country, c.name AS company
        FROM patents p
        JOIN relationships r ON p.patent_id   = r.patent_id
        JOIN inventors     i ON r.inventor_id  = i.inventor_id
        JOIN companies     c ON r.company_id   = c.company_id
        LIMIT :limit
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})

@st.cache_data
def load_ranked_inventors(limit=20):
    sql = """
        SELECT inventor_name, total_patents,
               RANK()       OVER (ORDER BY total_patents DESC) AS rank,
               DENSE_RANK() OVER (ORDER BY total_patents DESC) AS dense_rank,
               NTILE(4)     OVER (ORDER BY total_patents DESC) AS quartile
        FROM (
            SELECT i.name AS inventor_name, COUNT(r.patent_id) AS total_patents
            FROM relationships r
            JOIN inventors i ON r.inventor_id = i.inventor_id
            GROUP BY r.inventor_id
        ) ORDER BY total_patents DESC LIMIT :limit
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})

@st.cache_data
def load_inventor_productivity():
    sql = """
        SELECT patent_count, COUNT(*) AS num_inventors FROM (
            SELECT inventor_id, COUNT(patent_id) AS patent_count
            FROM relationships GROUP BY inventor_id
        ) GROUP BY patent_count ORDER BY patent_count ASC
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_yoy_growth():
    sql = """
        SELECT year, COUNT(*) AS patents FROM patents
        WHERE year IS NOT NULL GROUP BY year ORDER BY year ASC
    """
    df = pd.read_sql(text(sql), engine)
    df["prev_patents"] = df["patents"].shift(1)
    df["growth_pct"] = ((df["patents"] - df["prev_patents"]) / df["prev_patents"] * 100).round(1)
    return df.dropna(subset=["growth_pct"])

@st.cache_data
def load_top_inventors_by_country(limit=5):
    sql = """
        WITH top_countries AS (
            SELECT i.country FROM relationships r
            JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :limit
        ),
        inventor_counts AS (
            SELECT i.country, i.name AS inventor, COUNT(r.patent_id) AS patents,
                   RANK() OVER (PARTITION BY i.country ORDER BY COUNT(r.patent_id) DESC) AS rnk
            FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IN (SELECT country FROM top_countries)
            GROUP BY i.country, r.inventor_id
        )
        SELECT country, inventor, patents FROM inventor_counts
        WHERE rnk <= 3 ORDER BY country, patents DESC
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})

@st.cache_data
def load_company_inventor_ratio():
    sql = """
        SELECT c.name AS company,
               COUNT(DISTINCT r.inventor_id) AS unique_inventors,
               COUNT(DISTINCT r.patent_id)   AS total_patents,
               ROUND(CAST(COUNT(DISTINCT r.inventor_id) AS FLOAT) /
                     CAST(COUNT(DISTINCT r.patent_id)   AS FLOAT), 2) AS inventors_per_patent
        FROM relationships r JOIN companies c ON r.company_id = c.company_id
        GROUP BY r.company_id HAVING total_patents >= 2
        ORDER BY total_patents DESC LIMIT 10
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_country_share():
    sql = """
        SELECT i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY i.country ORDER BY patents DESC LIMIT 8
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_patents_per_year_per_country(limit=5):
    sql = """
        WITH top_countries AS (
            SELECT i.country FROM relationships r
            JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :limit
        )
        SELECT p.year, i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN patents p ON r.patent_id = p.patent_id
        WHERE i.country IN (SELECT country FROM top_countries) AND p.year IS NOT NULL
        GROUP BY p.year, i.country ORDER BY p.year ASC
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})

@st.cache_data
def load_country_company_matrix(top_n_countries=6, top_n_companies=6):
    sql = """
        WITH top_countries AS (
            SELECT i.country FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :nc
        ),
        top_companies AS (
            SELECT c.name AS company FROM relationships r JOIN companies c ON r.company_id = c.company_id
            GROUP BY c.name ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :nco
        )
        SELECT i.country, c.name AS company, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN companies c ON r.company_id = c.company_id
        WHERE i.country IN (SELECT country FROM top_countries)
          AND c.name    IN (SELECT company FROM top_companies)
        GROUP BY i.country, c.name ORDER BY patents DESC
    """
    return pd.read_sql(text(sql), engine, params={"nc": top_n_countries, "nco": top_n_companies})

@st.cache_data
def load_inventor_country_heatmap(top_n_countries=6, top_n_inventors=8):
    sql = """
        WITH top_countries AS (
            SELECT i.country FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :nc
        ),
        top_inventors AS (
            SELECT r.inventor_id FROM relationships r
            GROUP BY r.inventor_id ORDER BY COUNT(r.patent_id) DESC LIMIT :ni
        )
        SELECT i.name AS inventor, i.country, COUNT(r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IN (SELECT country FROM top_countries)
          AND r.inventor_id IN (SELECT inventor_id FROM top_inventors)
        GROUP BY i.name, i.country
    """
    return pd.read_sql(text(sql), engine, params={"nc": top_n_countries, "ni": top_n_inventors})

@st.cache_data
def load_company_yearly_top5():
    sql = """
        WITH top5 AS (
            SELECT c.name AS company FROM relationships r JOIN companies c ON r.company_id = c.company_id
            GROUP BY c.name ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT 5
        )
        SELECT p.year, c.name AS company, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN companies c ON r.company_id = c.company_id
        JOIN patents p ON r.patent_id = p.patent_id
        WHERE c.name IN (SELECT company FROM top5) AND p.year IS NOT NULL
        GROUP BY p.year, c.name ORDER BY p.year ASC
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_cumulative_patents_by_country(limit=5):
    sql = """
        WITH top_countries AS (
            SELECT i.country FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :limit
        )
        SELECT p.year, i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN patents p ON r.patent_id = p.patent_id
        WHERE i.country IN (SELECT country FROM top_countries) AND p.year IS NOT NULL
        GROUP BY p.year, i.country ORDER BY p.year ASC
    """
    df = pd.read_sql(text(sql), engine, params={"limit": limit})
    if df.empty:
        return df
    pivot = df.pivot(index="year", columns="country", values="patents").fillna(0)
    cumulative = pivot.cumsum().reset_index()
    return cumulative.melt(id_vars="year", var_name="country", value_name="cumulative_patents")

@st.cache_data
def load_inventor_efficiency():
    sql = """
        SELECT c.name AS company,
               COUNT(DISTINCT r.inventor_id) AS inventors,
               COUNT(DISTINCT r.patent_id)   AS patents,
               ROUND(CAST(COUNT(DISTINCT r.patent_id) AS FLOAT) /
                     CAST(COUNT(DISTINCT r.inventor_id) AS FLOAT), 2) AS patents_per_inventor
        FROM relationships r JOIN companies c ON r.company_id = c.company_id
        GROUP BY r.company_id HAVING patents >= 3
        ORDER BY patents_per_inventor DESC LIMIT 15
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_country_yoy():
    sql = """
        WITH top4 AS (
            SELECT i.country FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT 4
        )
        SELECT p.year, i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN patents p ON r.patent_id = p.patent_id
        WHERE i.country IN (SELECT country FROM top4) AND p.year IS NOT NULL
        GROUP BY p.year, i.country ORDER BY i.country, p.year ASC
    """
    df = pd.read_sql(text(sql), engine)
    if df.empty:
        return df
    df["prev"] = df.groupby("country")["patents"].shift(1)
    df["yoy_pct"] = ((df["patents"] - df["prev"]) / df["prev"] * 100).round(1)
    return df.dropna(subset=["yoy_pct"])

@st.cache_data
def load_company_country_diversity():
    sql = """
        SELECT c.name AS company,
               COUNT(DISTINCT i.country) AS countries_represented,
               COUNT(DISTINCT r.inventor_id) AS total_inventors,
               COUNT(DISTINCT r.patent_id)   AS total_patents
        FROM relationships r JOIN companies c ON r.company_id = c.company_id
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY r.company_id HAVING total_patents >= 2
        ORDER BY countries_represented DESC LIMIT 12
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_patent_age_distribution():
    sql = """
        SELECT CASE
            WHEN year < 1990 THEN 'Pre-1990'
            WHEN year BETWEEN 1990 AND 1999 THEN '1990s'
            WHEN year BETWEEN 2000 AND 2009 THEN '2000s'
            WHEN year BETWEEN 2010 AND 2019 THEN '2010s'
            ELSE '2020s'
        END AS decade, COUNT(*) AS patents
        FROM patents WHERE year IS NOT NULL
        GROUP BY decade ORDER BY MIN(year)
    """
    return pd.read_sql(text(sql), engine)

# ================================================================
# NEW DATA LOADERS (existing)
# ================================================================

@st.cache_data
def load_inventor_quartile_distribution():
    sql = """
        SELECT
            CASE
                WHEN total_patents = 1 THEN 'Single Patent'
                WHEN total_patents BETWEEN 2 AND 3 THEN '2-3 Patents'
                WHEN total_patents BETWEEN 4 AND 9 THEN '4-9 Patents'
                ELSE '10+ Patents'
            END AS tier,
            COUNT(*) AS inventors
        FROM (
            SELECT inventor_id, COUNT(patent_id) AS total_patents
            FROM relationships GROUP BY inventor_id
        )
        GROUP BY tier
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_company_patent_share(limit=8):
    sql = """
        SELECT c.name AS company, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN companies c ON r.company_id = c.company_id
        GROUP BY r.company_id ORDER BY patents DESC LIMIT :limit
    """
    df = pd.read_sql(text(sql), engine, params={"limit": limit})
    total = pd.read_sql(text("SELECT COUNT(*) AS n FROM patents"), engine).iloc[0]["n"]
    df["share"] = df["patents"] / total * 100
    others = total - df["patents"].sum()
    if others > 0:
        other_row = pd.DataFrame([{"company": "Others", "patents": others,
                                   "share": others / total * 100}])
        df = pd.concat([df, other_row], ignore_index=True)
    return df

@st.cache_data
def load_country_share_extended(limit=10):
    sql = """
        SELECT i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY i.country ORDER BY patents DESC LIMIT :limit
    """
    df = pd.read_sql(text(sql), engine, params={"limit": limit})
    total = df["patents"].sum()
    df["share"] = df["patents"] / total * 100
    return df

@st.cache_data
def load_decade_share():
    sql = """
        SELECT CASE
            WHEN year < 1990 THEN 'Pre-1990'
            WHEN year BETWEEN 1990 AND 1999 THEN '1990s'
            WHEN year BETWEEN 2000 AND 2009 THEN '2000s'
            WHEN year BETWEEN 2010 AND 2019 THEN '2010s'
            ELSE '2020s'
        END AS decade, COUNT(*) AS patents
        FROM patents WHERE year IS NOT NULL
        GROUP BY decade ORDER BY MIN(year)
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_top_company_country_breakdown(top_n=5):
    sql = """
        WITH top_companies AS (
            SELECT c.name AS company FROM relationships r
            JOIN companies c ON r.company_id = c.company_id
            GROUP BY c.name ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :top_n
        )
        SELECT c.name AS company, i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN companies c ON r.company_id = c.company_id
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE c.name IN (SELECT company FROM top_companies)
          AND i.country IS NOT NULL AND i.country != ''
        GROUP BY c.name, i.country
        ORDER BY c.name, patents DESC
    """
    return pd.read_sql(text(sql), engine, params={"top_n": top_n})

@st.cache_data
def load_inventor_collaboration_tiers():
    sql = """
        SELECT
            CASE
                WHEN inventor_count = 1 THEN 'Solo'
                WHEN inventor_count BETWEEN 2 AND 3 THEN '2-3 inventors'
                WHEN inventor_count BETWEEN 4 AND 6 THEN '4-6 inventors'
                ELSE '7+ inventors'
            END AS collab_tier,
            COUNT(*) AS patents
        FROM (
            SELECT patent_id, COUNT(DISTINCT inventor_id) AS inventor_count
            FROM relationships GROUP BY patent_id
        )
        GROUP BY collab_tier
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_company_size_tiers():
    sql = """
        SELECT
            CASE
                WHEN total_patents = 1 THEN '1 patent'
                WHEN total_patents BETWEEN 2 AND 5 THEN '2-5 patents'
                WHEN total_patents BETWEEN 6 AND 20 THEN '6-20 patents'
                ELSE '20+ patents'
            END AS size_tier,
            COUNT(*) AS companies
        FROM (
            SELECT company_id, COUNT(DISTINCT patent_id) AS total_patents
            FROM relationships GROUP BY company_id
        )
        GROUP BY size_tier
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_country_inventor_density():
    sql = """
        SELECT i.country,
               COUNT(DISTINCT r.inventor_id) AS inventors,
               COUNT(DISTINCT r.patent_id) AS patents,
               ROUND(CAST(COUNT(DISTINCT r.patent_id) AS FLOAT) /
                     CAST(COUNT(DISTINCT r.inventor_id) AS FLOAT), 2) AS patents_per_inventor
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY i.country HAVING inventors >= 2
        ORDER BY patents DESC LIMIT 10
    """
    return pd.read_sql(text(sql), engine)

@st.cache_data
def load_filing_decade_by_country(limit=5):
    sql = """
        WITH top_countries AS (
            SELECT i.country FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC LIMIT :limit
        )
        SELECT
            CASE
                WHEN p.year < 1990 THEN 'Pre-1990'
                WHEN p.year BETWEEN 1990 AND 1999 THEN '1990s'
                WHEN p.year BETWEEN 2000 AND 2009 THEN '2000s'
                WHEN p.year BETWEEN 2010 AND 2019 THEN '2010s'
                ELSE '2020s'
            END AS decade,
            i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN patents p ON r.patent_id = p.patent_id
        WHERE i.country IN (SELECT country FROM top_countries) AND p.year IS NOT NULL
        GROUP BY decade, i.country ORDER BY MIN(p.year), i.country
    """
    return pd.read_sql(text(sql), engine, params={"limit": limit})


# ================================================================
# MAP DATA LOADERS  (NEW — Comparative Map page)
# ================================================================

@st.cache_data
def load_all_countries_patents():
    """All countries with total patent counts — for the choropleth."""
    sql = """
        SELECT i.country,
               COUNT(DISTINCT r.patent_id)   AS patents,
               COUNT(DISTINCT r.inventor_id) AS inventors,
               COUNT(DISTINCT r.company_id)  AS companies
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE i.country IS NOT NULL AND i.country != ''
        GROUP BY i.country
        ORDER BY patents DESC
    """
    return pd.read_sql(text(sql), engine)


@st.cache_data
def load_country_yearly_all():
    """Year × country patent counts — for sparklines & growth calculations."""
    sql = """
        SELECT p.year, i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN patents p   ON r.patent_id   = p.patent_id
        WHERE i.country IS NOT NULL AND i.country != ''
          AND p.year IS NOT NULL
        GROUP BY p.year, i.country
        ORDER BY i.country, p.year
    """
    return pd.read_sql(text(sql), engine)


@st.cache_data
def load_country_top_companies(limit_countries=10, limit_companies=3):
    """Top companies per country — for the comparison table."""
    sql = """
        WITH top_countries AS (
            SELECT i.country FROM relationships r
            JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country IS NOT NULL AND i.country != ''
            GROUP BY i.country ORDER BY COUNT(DISTINCT r.patent_id) DESC
            LIMIT :lc
        ),
        ranked AS (
            SELECT i.country, c.name AS company,
                   COUNT(DISTINCT r.patent_id) AS patents,
                   RANK() OVER (PARTITION BY i.country
                                ORDER BY COUNT(DISTINCT r.patent_id) DESC) AS rnk
            FROM relationships r
            JOIN inventors i ON r.inventor_id = i.inventor_id
            JOIN companies c ON r.company_id  = c.company_id
            WHERE i.country IN (SELECT country FROM top_countries)
            GROUP BY i.country, c.name
        )
        SELECT country, company, patents FROM ranked
        WHERE rnk <= :lco
        ORDER BY country, patents DESC
    """
    return pd.read_sql(text(sql), engine,
                       params={"lc": limit_countries, "lco": limit_companies})


@st.cache_data
def load_country_decade_pivot():
    """Decade × country pivot — for the side-by-side decade breakdown."""
    sql = """
        SELECT
            CASE
                WHEN p.year < 1990            THEN 'Pre-1990'
                WHEN p.year BETWEEN 1990 AND 1999 THEN '1990s'
                WHEN p.year BETWEEN 2000 AND 2009 THEN '2000s'
                WHEN p.year BETWEEN 2010 AND 2019 THEN '2010s'
                ELSE '2020s'
            END AS decade,
            i.country,
            COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN patents   p ON r.patent_id   = p.patent_id
        WHERE i.country IS NOT NULL AND i.country != ''
          AND p.year IS NOT NULL
        GROUP BY decade, i.country
    """
    return pd.read_sql(text(sql), engine)


# ================================================================
# CHART HELPERS (original)
# ================================================================

def _fig(w=9, h=4.5):
    return plt.subplots(figsize=(w, h))


def _smooth(x, y, points=300):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    if len(x) < 4:
        return x, y
    try:
        x_new = np.linspace(x.min(), x.max(), points)
        spline = make_interp_spline(x, y, k=3)
        y_new = spline(x_new)
        return x_new, y_new
    except Exception:
        return x, y


def _add_gradient_fill(ax, x, y, color, alpha_top=0.22, alpha_bottom=0.02, zorder=2):
    steps = 40
    y_min = ax.get_ylim()[0] if ax.get_ylim()[0] != ax.get_ylim()[1] else 0
    for i in range(steps):
        frac = i / steps
        alpha = alpha_top * (1 - frac) ** 1.8 + alpha_bottom
        y_upper = y_min + (y - y_min) * (1 - frac / steps)
        y_lower = y_min + (y - y_min) * (1 - (frac + 1) / steps)
        ax.fill_between(x, y_lower, y_upper, alpha=alpha, color=color, zorder=zorder, linewidth=0)


def _end_label(ax, x_val, y_val, text, color, fontsize=7.5, offset=(6, 2)):
    ax.annotate(
        text,
        xy=(x_val, y_val),
        xytext=(offset[0], offset[1]),
        textcoords="offset points",
        fontsize=fontsize,
        color=color,
        fontweight="600",
        path_effects=[
            pe.withStroke(linewidth=3, foreground=BG_PLOT)
        ],
    )


def bar_chart(df, x_col, y_col, title, color):
    fig, ax = _fig()
    bars = ax.bar(df[x_col], df[y_col], color=color, edgecolor=BG_CARD, linewidth=0.8,
                  width=0.65, zorder=3)
    for bar in bars:
        bar.set_alpha(0.88)
    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.set_ylabel("Patents", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    plt.xticks(rotation=35, ha="right", fontsize=8)
    for bar in bars:
        h_val = bar.get_height()
        if h_val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h_val + 0.15,
                    f"{int(h_val):,}", ha="center", va="bottom",
                    fontsize=7.5, color=TEXT_2)
    plt.tight_layout(pad=1.4)
    return fig


def line_chart(df, x_col, y_col, title, color=None, annotate_last=True):
    color = color or ACCENT
    fig, ax = _fig()

    x_raw = df[x_col].values.astype(float)
    y_raw = df[y_col].values.astype(float)
    x_sm, y_sm = _smooth(x_raw, y_raw)

    ax.set_ylim(0, y_raw.max() * 1.15)
    _add_gradient_fill(ax, x_sm, y_sm, color)

    ax.plot(x_sm, y_sm, color=color, linewidth=2.4, zorder=5, solid_capstyle="round")
    ax.scatter(x_raw, y_raw, color=color, s=28, zorder=6,
               edgecolors=BG_PLOT, linewidths=1.5)

    peak_idx = np.argmax(y_raw)
    ax.axhline(y_raw[peak_idx], color=color, linewidth=0.5,
               linestyle=":", alpha=0.35, zorder=3)

    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel(x_col.capitalize(), fontsize=9)
    ax.set_ylabel(y_col.replace("_", " ").title(), fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    if annotate_last and len(df) > 0:
        last = df.iloc[-1]
        _end_label(ax, last[x_col], last[y_col],
                   f"{int(last[y_col]):,}", color, fontsize=8)

    plt.tight_layout(pad=1.4)
    return fig


def multi_line_chart(df, x_col, y_col, group_col, title, colors=None, annotate=True):
    colors = colors or PALETTE
    groups = df[group_col].unique()
    fig, ax = _fig(10, 5)

    y_max = df[y_col].max() * 1.2
    ax.set_ylim(0, y_max)

    for i, grp in enumerate(groups):
        sub = df[df[group_col] == grp].sort_values(x_col)
        c = colors[i % len(colors)]

        x_raw = sub[x_col].values.astype(float)
        y_raw = sub[y_col].values.astype(float)
        x_sm, y_sm = _smooth(x_raw, y_raw)

        ax.fill_between(x_sm, y_sm, alpha=0.07, color=c, zorder=2)
        ax.plot(x_sm, y_sm, color=c, linewidth=2.2,
                label=str(grp)[:22], zorder=5, solid_capstyle="round")
        ax.scatter(x_raw, y_raw, color=c, s=20, zorder=6,
                   edgecolors=BG_PLOT, linewidths=1.2, alpha=0.9)

        if annotate and len(sub) > 0:
            last = sub.iloc[-1]
            _end_label(ax, last[x_col], last[y_col], str(grp)[:14], c)

    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel(x_col.capitalize(), fontsize=9)
    ax.set_ylabel(y_col.replace("_", " ").title(), fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(loc="upper left", fontsize=8, framealpha=0.7)
    plt.tight_layout(pad=1.4)
    return fig


def growth_bar_chart(df, x_col, y_col, title):
    fig, ax = _fig()
    bar_colors = [ACCENT2 if v >= 0 else ACCENT4 for v in df[y_col]]
    bars = ax.bar(df[x_col], df[y_col], color=bar_colors, edgecolor=BG_CARD,
                  linewidth=0.6, width=0.7, zorder=3, alpha=0.88)

    ax.axhline(0, color=TEXT_2, linewidth=1.2, linestyle="-", alpha=0.5, zorder=4)

    if len(df) >= 4:
        x_r = df[x_col].values.astype(float)
        y_r = df[y_col].values.astype(float)
        x_sm, y_sm = _smooth(x_r, y_r)
        ax.plot(x_sm, y_sm, color=ACCENT3, linewidth=1.6,
                linestyle="--", alpha=0.6, zorder=5, label="Trend")
        ax.legend(fontsize=7, loc="upper right", framealpha=0.5)

    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Growth (%)", fontsize=9)
    plt.xticks(rotation=35, ha="right", fontsize=8)
    plt.tight_layout(pad=1.4)
    return fig


def forecast_line_chart(df, x_col, y_col, title, forecast_years=5, color=ACCENT):
    fig, ax = _fig(10, 5)

    x_raw = df[x_col].values.astype(float)
    y_raw = df[y_col].values.astype(float)
    x_sm, y_sm = _smooth(x_raw, y_raw)

    y_top = max(y_raw.max(), 1) * 1.25
    ax.set_ylim(0, y_top)

    _add_gradient_fill(ax, x_sm, y_sm, color, alpha_top=0.18, alpha_bottom=0.01)
    ax.plot(x_sm, y_sm, color=color, linewidth=2.4, zorder=5,
            solid_capstyle="round", label="Actual")
    ax.scatter(x_raw, y_raw, color=color, s=24, zorder=6,
               edgecolors=BG_PLOT, linewidths=1.4)

    if len(x_raw) >= 2:
        coeffs = np.polyfit(x_raw, y_raw, 1)
        future_x = np.arange(x_raw[-1] + 1, x_raw[-1] + forecast_years + 1)
        forecast_y = np.maximum(np.polyval(coeffs, future_x), 0)

        ax.plot(x_raw, np.polyval(coeffs, x_raw),
                color=ACCENT3, linewidth=1.0, linestyle="--", alpha=0.45, zorder=3)
        ax.axvline(x=x_raw[-1], color=TEXT_2, linewidth=0.8,
                   linestyle=":", alpha=0.45, zorder=4)
        ax.text(x_raw[-1] + 0.15, y_top * 0.96, "forecast ->",
                fontsize=7, color=TEXT_2, alpha=0.6)

        ax.fill_between(future_x, forecast_y * 0.85, forecast_y * 1.15,
                        alpha=0.12, color=ACCENT3, zorder=2, label="+-15% CI")

        bridge_x = np.array([x_raw[-1], future_x[0]])
        bridge_y = np.array([y_raw[-1], forecast_y[0]])
        ax.plot(bridge_x, bridge_y, color=ACCENT3, linewidth=2.0,
                linestyle="--", alpha=0.8, zorder=5)

        if len(future_x) >= 4:
            fx_sm, fy_sm = _smooth(future_x, forecast_y)
            ax.plot(fx_sm, fy_sm, color=ACCENT3, linewidth=2.2,
                    linestyle="--", zorder=5,
                    label=f"Forecast (+{forecast_years}yr)")
        else:
            ax.plot(future_x, forecast_y, color=ACCENT3, linewidth=2.2,
                    linestyle="--", zorder=5,
                    label=f"Forecast (+{forecast_years}yr)")

        ax.scatter(future_x, forecast_y, color=ACCENT3, s=44, marker="s",
                   zorder=7, edgecolors=BG_PLOT, linewidths=1.4)

    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Patents", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(max(x,0)):,}"))
    ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
    plt.tight_layout(pad=1.4)
    return fig


def moving_avg_chart(df, x_col, y_col, title, windows=(3, 5), color=ACCENT):
    ma_colors = [ACCENT3, ACCENT4]
    fig, ax = _fig(10, 5)

    x_raw = df[x_col].values.astype(float)
    y_raw = df[y_col].values.astype(float)
    x_sm, y_sm = _smooth(x_raw, y_raw)

    ax.set_ylim(0, y_raw.max() * 1.18)

    ax.fill_between(x_sm, y_sm, alpha=0.06, color=color, zorder=2)
    ax.plot(x_sm, y_sm, color=color, linewidth=1.2, alpha=0.45,
            label="Annual (raw)", zorder=3, solid_capstyle="round")
    ax.scatter(x_raw, y_raw, color=color, s=14, zorder=4,
               edgecolors=BG_PLOT, linewidths=1.0, alpha=0.55)

    for i, w in enumerate(windows):
        if len(df) > w:
            ma_vals = df[y_col].rolling(w).mean().dropna().values
            ma_x = x_raw[w - 1:]
            x_ma_sm, y_ma_sm = _smooth(ma_x, ma_vals)
            c = ma_colors[i % len(ma_colors)]
            ax.fill_between(x_ma_sm, y_ma_sm, alpha=0.07, color=c, zorder=2)
            ax.plot(x_ma_sm, y_ma_sm, color=c, linewidth=2.4,
                    label=f"{w}-yr MA", zorder=5, solid_capstyle="round")
            _end_label(ax, ma_x[-1], ma_vals[-1], f"{w}-yr", c, fontsize=7)

    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Patents", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(max(x,0)):,}"))
    ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
    plt.tight_layout(pad=1.4)
    return fig


def cumulative_line_chart(df_long, x_col, y_col, group_col, title, colors=None):
    colors = colors or PALETTE
    groups = df_long[group_col].unique()
    fig, ax = _fig(10, 5)

    y_max = df_long[y_col].max() * 1.12
    ax.set_ylim(0, y_max)

    for i, grp in enumerate(groups):
        sub = df_long[df_long[group_col] == grp].sort_values(x_col)
        c = colors[i % len(colors)]

        x_raw = sub[x_col].values.astype(float)
        y_raw = sub[y_col].values.astype(float)
        x_sm, y_sm = _smooth(x_raw, y_raw)

        _add_gradient_fill(ax, x_sm, y_sm, c, alpha_top=0.15, alpha_bottom=0.01)
        ax.plot(x_sm, y_sm, color=c, linewidth=2.6, zorder=5,
                solid_capstyle="round", label=str(grp)[:20])
        ax.scatter(x_raw, y_raw, color=c, s=22, zorder=6,
                   edgecolors=BG_PLOT, linewidths=1.4)

        if len(sub) > 0:
            last = sub.iloc[-1]
            _end_label(ax, last[x_col], last[y_col],
                       str(grp)[:14], c, fontsize=7.5)

    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Cumulative Patents", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
    plt.tight_layout(pad=1.4)
    return fig


# ================================================================
# EXISTING CHART HELPERS — Donut / Nested Ring / Exploded Pie
# ================================================================

def donut_chart(labels, values, title, colors=None, center_label=None,
                center_sub=None, figsize=(7, 5)):
    colors = colors or PIE_PALETTE
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG_CARD)
    ax.set_facecolor(BG_CARD)

    total = sum(values)
    pcts = [v / total * 100 for v in values]
    max_idx = values.index(max(values))
    explode = [0.03 if i == max_idx else 0.0 for i in range(len(values))]

    wedges, _ = ax.pie(
        values,
        explode=explode,
        colors=[colors[i % len(colors)] for i in range(len(labels))],
        startangle=90,
        wedgeprops=dict(width=0.52, edgecolor=BG_CARD, linewidth=2.5),
        counterclock=False,
    )

    inner_ring = plt.Circle((0, 0), 0.47, color=BG_CARD, zorder=3)
    ax.add_patch(inner_ring)

    for i, (wedge, pct) in enumerate(zip(wedges, pcts)):
        if pct >= 4.0:
            angle = (wedge.theta2 + wedge.theta1) / 2
            rad = 0.75
            x = rad * np.cos(np.radians(angle))
            y = rad * np.sin(np.radians(angle))
            ax.text(x, y, f"{pct:.1f}%",
                    ha="center", va="center", fontsize=7.5,
                    fontweight="700", color="white",
                    path_effects=[pe.withStroke(linewidth=2.5, foreground=BG_CARD)])

    if center_label:
        ax.text(0, 0.10, center_label, ha="center", va="center",
                fontsize=17, fontweight="700", color=TEXT_1)
    if center_sub:
        ax.text(0, -0.16, center_sub, ha="center", va="center",
                fontsize=8, color=TEXT_2)

    legend_labels = [
        f"{l[:20]}  {v:,} ({p:.1f}%)"
        for l, v, p in zip(labels, values, pcts)
    ]
    legend_patches = [
        mpatches.Patch(facecolor=colors[i % len(colors)], edgecolor="none")
        for i in range(len(labels))
    ]
    ax.legend(
        handles=legend_patches,
        labels=legend_labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=7.5,
        framealpha=0.0,
        handlelength=1.0,
        handleheight=1.0,
    )

    ax.set_title(title, fontsize=13, fontweight="600", pad=14, color=TEXT_1)
    plt.tight_layout()
    return fig


def nested_donut_chart(outer_labels, outer_values,
                       inner_labels, inner_values,
                       title, outer_colors=None, inner_colors=None,
                       figsize=(7.5, 5.5)):
    outer_colors = outer_colors or PIE_PALETTE
    inner_colors = inner_colors or [c + "bb" for c in PIE_PALETTE]

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG_CARD)
    ax.set_facecolor(BG_CARD)

    total_out = sum(outer_values)

    outer_wedges, _ = ax.pie(
        outer_values,
        colors=[outer_colors[i % len(outer_colors)] for i in range(len(outer_labels))],
        radius=1.0,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.36, edgecolor=BG_CARD, linewidth=2.2),
    )
    inner_wedges, _ = ax.pie(
        inner_values,
        colors=[outer_colors[i % len(outer_colors)]
                for i in range(len(inner_labels))],
        radius=0.62,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.30, edgecolor=BG_CARD, linewidth=1.5, alpha=0.65),
    )

    ax.text(0, 0.06, f"{total_out:,}", ha="center", va="center",
            fontsize=15, fontweight="700", color=TEXT_1)
    ax.text(0, -0.12, "patents", ha="center", va="center",
            fontsize=8, color=TEXT_2)

    for i, (wedge, lbl) in enumerate(zip(outer_wedges, outer_labels)):
        pct = outer_values[i] / total_out * 100
        if pct >= 5:
            angle = (wedge.theta2 + wedge.theta1) / 2
            x = 0.82 * np.cos(np.radians(angle))
            y = 0.82 * np.sin(np.radians(angle))
            ax.text(x, y, f"{pct:.0f}%", ha="center", va="center",
                    fontsize=7, fontweight="700", color="white",
                    path_effects=[pe.withStroke(linewidth=2, foreground=BG_CARD)])

    patches = [
        mpatches.Patch(facecolor=outer_colors[i % len(outer_colors)], edgecolor="none")
        for i in range(len(outer_labels))
    ]
    ax.legend(handles=patches, labels=[l[:22] for l in outer_labels],
              loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=7.5, framealpha=0.0)

    ax.set_title(title, fontsize=13, fontweight="600", pad=14, color=TEXT_1)
    plt.tight_layout()
    return fig


def exploded_pie_chart(labels, values, title, colors=None,
                       highlight_n=1, figsize=(7, 5)):
    colors = colors or PIE_PALETTE
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG_CARD)
    ax.set_facecolor(BG_CARD)

    sorted_idx = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    explode = [0.06 if i in sorted_idx[:highlight_n] else 0.0
               for i in range(len(values))]

    def autopct_func(pct):
        return f"{pct:.1f}%" if pct >= 5.0 else ""

    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        autopct=autopct_func,
        explode=explode,
        colors=[colors[i % len(colors)] for i in range(len(labels))],
        startangle=140,
        counterclock=False,
        wedgeprops=dict(edgecolor=BG_CARD, linewidth=2.2, joinstyle="round"),
        pctdistance=0.78,
        shadow=False,
    )

    for at in autotexts:
        at.set_fontsize(7.5)
        at.set_fontweight("700")
        at.set_color("white")
        at.set_path_effects([pe.withStroke(linewidth=2, foreground=BG_CARD)])

    patches = [
        mpatches.Patch(facecolor=colors[i % len(colors)], edgecolor="none")
        for i in range(len(labels))
    ]
    legend_labels = [f"{l[:20]}  ({v:,})" for l, v in zip(labels, values)]
    ax.legend(handles=patches, labels=legend_labels,
              loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=7.5, framealpha=0.0)

    ax.set_title(title, fontsize=13, fontweight="600", pad=14, color=TEXT_1)
    plt.tight_layout()
    return fig


def radial_bar_chart(labels, values, title, colors=None, figsize=(7, 7)):
    colors = colors or PIE_PALETTE
    n = len(labels)
    max_val = max(values) if values else 1

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(BG_CARD)
    ax.set_facecolor(BG_CARD)

    theta = np.linspace(0.1, 2 * np.pi - 0.1, n, endpoint=False)
    width = (2 * np.pi - 0.2) / n * 0.82

    for i, (angle, val, lbl) in enumerate(zip(theta, values, labels)):
        c = colors[i % len(colors)]
        norm_val = val / max_val
        ax.bar(angle, 1.0, width=width, bottom=0.05,
               color=BORDER_C, alpha=0.5, zorder=2)
        ax.bar(angle, norm_val, width=width, bottom=0.05,
               color=c, alpha=0.88, zorder=3,
               edgecolor=BG_CARD, linewidth=1.0)
        label_r = 1.18
        ax.text(angle, label_r, lbl[:14],
                ha="center", va="center", fontsize=7.5,
                color=TEXT_1, fontweight="600",
                rotation=np.degrees(angle) - 90 if angle > np.pi else np.degrees(angle) + 90)
        ax.text(angle, norm_val + 0.07, f"{val:,}",
                ha="center", va="center", fontsize=6.5,
                color=c, fontweight="700",
                path_effects=[pe.withStroke(linewidth=2, foreground=BG_CARD)])

    ax.set_ylim(0, 1.45)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.grid(False)
    ax.set_title(title, fontsize=13, fontweight="600", pad=18, color=TEXT_1)
    fig.patch.set_facecolor(BG_CARD)
    plt.tight_layout()
    return fig


def stacked_donut_small_multiples(groups_data, suptitle, figsize=None):
    n = len(groups_data)
    cols = min(n, 3)
    rows = (n + cols - 1) // cols
    if figsize is None:
        figsize = (cols * 3.8, rows * 3.8)

    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    fig.patch.set_facecolor(BG_CARD)

    if n == 1:
        axes = [axes]
    else:
        axes = np.array(axes).flatten()

    for idx, (grp_label, sub_labels, sub_values) in enumerate(groups_data):
        ax = axes[idx]
        ax.set_facecolor(BG_CARD)
        total = sum(sub_values)

        wedges, _ = ax.pie(
            sub_values,
            colors=[PIE_PALETTE[i % len(PIE_PALETTE)] for i in range(len(sub_labels))],
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.48, edgecolor=BG_CARD, linewidth=2.0),
        )
        inner = plt.Circle((0, 0), 0.50, color=BG_CARD, zorder=3)
        ax.add_patch(inner)

        for i, (wedge, sv) in enumerate(zip(wedges, sub_values)):
            pct = sv / total * 100
            if pct >= 10:
                angle = (wedge.theta2 + wedge.theta1) / 2
                x = 0.72 * np.cos(np.radians(angle))
                y = 0.72 * np.sin(np.radians(angle))
                ax.text(x, y, f"{pct:.0f}%", ha="center", va="center",
                        fontsize=7, fontweight="700", color="white",
                        path_effects=[pe.withStroke(linewidth=2, foreground=BG_CARD)])

        ax.text(0, 0.07, f"{total:,}", ha="center", va="center",
                fontsize=11, fontweight="700", color=TEXT_1)
        ax.text(0, -0.17, "patents", ha="center", va="center",
                fontsize=7, color=TEXT_2)
        ax.set_title(grp_label[:22], fontsize=9, fontweight="600",
                     color=TEXT_1, pad=8)

    for idx in range(n, len(axes)):
        axes[idx].set_visible(False)

    all_labels = []
    for _, sl, _ in groups_data:
        all_labels.extend(sl[:3])
    unique_labels = list(dict.fromkeys(all_labels))[:8]
    patches = [mpatches.Patch(facecolor=PIE_PALETTE[i % len(PIE_PALETTE)], edgecolor="none")
               for i in range(len(unique_labels))]
    fig.legend(handles=patches, labels=unique_labels,
               loc="lower center", ncol=min(len(unique_labels), 4),
               fontsize=7.5, framealpha=0.0, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(suptitle, fontsize=13, fontweight="700",
                 color=TEXT_1, y=1.01)
    plt.tight_layout()
    return fig


# ================================================================
# MAP CHART HELPERS  (NEW — Comparative Map page)
# ================================================================

# Comprehensive country-name → ISO-3 lookup table
# Covers 2-letter codes, common abbreviations, and full names
_NAME_TO_ISO3 = {
    # 2-letter ISO codes
    "US": "USA", "JP": "JPN", "DE": "DEU", "GB": "GBR", "CN": "CHN",
    "FR": "FRA", "KR": "KOR", "CA": "CAN", "CH": "CHE", "NL": "NLD",
    "SE": "SWE", "AU": "AUS", "IT": "ITA", "ES": "ESP", "IN": "IND",
    "IL": "ISR", "TW": "TWN", "SG": "SGP", "BE": "BEL", "AT": "AUT",
    "DK": "DNK", "FI": "FIN", "NO": "NOR", "BR": "BRA", "RU": "RUS",
    # Full / common names
    "United States": "USA", "USA": "USA",
    "Japan": "JPN",
    "Germany": "DEU",
    "United Kingdom": "GBR", "UK": "GBR",
    "China": "CHN", "People's Republic of China": "CHN",
    "France": "FRA",
    "South Korea": "KOR", "Korea": "KOR", "Republic of Korea": "KOR",
    "Canada": "CAN",
    "Switzerland": "CHE",
    "Netherlands": "NLD",
    "Sweden": "SWE",
    "Australia": "AUS",
    "Italy": "ITA",
    "Spain": "ESP",
    "India": "IND",
    "Israel": "ISR",
    "Taiwan": "TWN", "Republic of China": "TWN",
    "Singapore": "SGP",
    "Belgium": "BEL",
    "Austria": "AUT",
    "Denmark": "DNK",
    "Finland": "FIN",
    "Norway": "NOR",
    "Brazil": "BRA",
    "Russia": "RUS", "Russian Federation": "RUS",
    "Poland": "POL",
    "Czech Republic": "CZE", "Czechia": "CZE",
    "Hungary": "HUN",
    "New Zealand": "NZL",
    "Mexico": "MEX",
    "Argentina": "ARG",
    "South Africa": "ZAF",
}


def _resolve_iso3(name: str) -> str | None:
    """Convert a country name/code to ISO-3. Falls back to pycountry fuzzy search."""
    if not name:
        return None
    # Direct lookup first
    iso = _NAME_TO_ISO3.get(name)
    if iso:
        return iso
    # Try pycountry if available
    if _HAS_PYCOUNTRY:
        try:
            matches = pycountry.countries.search_fuzzy(name)
            if matches:
                return matches[0].alpha_3
        except Exception:
            pass
    return None


def _build_geo_df(df_country: pd.DataFrame) -> pd.DataFrame:
    """Add iso3 column to a country-level DataFrame."""
    df = df_country.copy()
    df["iso3"] = df["country"].apply(_resolve_iso3)
    return df.dropna(subset=["iso3"])


def build_choropleth(df_geo: pd.DataFrame, metric: str = "patents",
                     title: str = "Patent Output by Country",
                     colorscale: str = "Blues") -> go.Figure:
    """
    Interactive Plotly choropleth world map.
    df_geo must have columns: iso3, country, patents (+ optionally inventors, companies).
    """
    hover_text = []
    for _, row in df_geo.iterrows():
        lines = [f"<b>{row['country']}</b>",
                 f"Patents: {int(row['patents']):,}"]
        if "inventors" in row:
            lines.append(f"Inventors: {int(row['inventors']):,}")
        if "companies" in row:
            lines.append(f"Companies: {int(row['companies']):,}")
        if "share_pct" in row:
            lines.append(f"Global share: {row['share_pct']:.1f}%")
        hover_text.append("<br>".join(lines))

    fig = go.Figure(go.Choropleth(
        locations=df_geo["iso3"],
        z=df_geo[metric],
        locationmode="ISO-3",
        colorscale=colorscale,
        reversescale=False,
        text=hover_text,
        hovertemplate="%{text}<extra></extra>",
        colorbar=dict(
            title=dict(text=metric.replace("_", " ").title(), font=dict(color="#7b8db0", size=10)),
            tickfont=dict(color="#7b8db0", size=9),
            bgcolor="rgba(14,17,23,0.8)",
            bordercolor="#1e2433",
            borderwidth=1,
            len=0.75,
            thickness=14,
            x=1.01,
        ),
        marker_line_color="#1e2433",
        marker_line_width=0.5,
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color="#eaf0fb", size=14, family="Space Grotesk"),
                   x=0.01, y=0.98),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#1e2433",
            showland=True,
            landcolor="#111827",
            showocean=True,
            oceancolor="#07090f",
            showcountries=True,
            countrycolor="#1e2433",
            showlakes=False,
            bgcolor="#07090f",
            projection_type="natural earth",
        ),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=0, r=0, t=32, b=0),
        height=480,
        font=dict(family="Space Grotesk", color="#7b8db0"),
    )
    return fig


def build_bubble_map(df_geo: pd.DataFrame,
                     title: str = "Patent Bubble Map") -> go.Figure:
    """
    Scatter-geo bubble map — bubble size = patents, colour = inventors per patent.
    Complementary view to the choropleth.
    """
    # Approximate centroids for the ISO3 codes we know about
    # Plotly resolves these automatically from the ISO-3 code
    df = df_geo.copy()
    df["eff"] = df["patents"] / df["inventors"].clip(lower=1)
    df["size_scaled"] = np.sqrt(df["patents"]) * 2.5

    hover_text = []
    for _, row in df.iterrows():
        hover_text.append(
            f"<b>{row['country']}</b><br>"
            f"Patents: {int(row['patents']):,}<br>"
            f"Inventors: {int(row['inventors']):,}<br>"
            f"Efficiency: {row['eff']:.2f} pat/inv"
        )

    fig = go.Figure(go.Scattergeo(
        locations=df["iso3"],
        locationmode="ISO-3",
        mode="markers",
        marker=dict(
            size=df["size_scaled"].clip(upper=60),
            color=df["eff"],
            colorscale="Viridis",
            reversescale=False,
            opacity=0.82,
            line=dict(color="#1e2433", width=0.8),
            colorbar=dict(
                title=dict(text="Pat/Inv", font=dict(color="#7b8db0", size=9)),
                tickfont=dict(color="#7b8db0", size=8),
                bgcolor="rgba(14,17,23,0.8)",
                bordercolor="#1e2433",
                borderwidth=1,
                len=0.65,
                thickness=12,
                x=1.01,
            ),
            sizemode="diameter",
        ),
        text=hover_text,
        hovertemplate="%{text}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color="#eaf0fb", size=14, family="Space Grotesk"),
                   x=0.01, y=0.98),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#1e2433",
            showland=True,
            landcolor="#111827",
            showocean=True,
            oceancolor="#07090f",
            showcountries=True,
            countrycolor="#1e2433",
            showlakes=False,
            bgcolor="#07090f",
            projection_type="natural earth",
        ),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=0, r=0, t=32, b=0),
        height=460,
        font=dict(family="Space Grotesk", color="#7b8db0"),
    )
    return fig


def comparison_bar_mpl(df_sel: pd.DataFrame, metric: str = "patents",
                       title: str = "") -> plt.Figure:
    """
    Horizontal bar chart comparing selected countries on a chosen metric.
    Each bar colour-coded by rank.
    """
    df_s = df_sel.sort_values(metric, ascending=True).reset_index(drop=True)
    n = len(df_s)
    colors_bar = [PIE_PALETTE[i % len(PIE_PALETTE)] for i in range(n)]

    fig, ax = _fig(8, max(3.5, n * 0.52))
    bars = ax.barh(df_s["country"], df_s[metric],
                   color=colors_bar, edgecolor=BG_CARD,
                   linewidth=0.7, height=0.62, alpha=0.88, zorder=3)

    for bar, val in zip(bars, df_s[metric]):
        ax.text(val + df_s[metric].max() * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", ha="left",
                fontsize=8, color=TEXT_2, fontweight="600")

    ax.set_xlabel(metric.replace("_", " ").title(), fontsize=9)
    ax.set_title(title or f"Country Comparison — {metric.title()}", fontsize=12,
                 fontweight="600", pad=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(0, df_s[metric].max() * 1.18)
    plt.tight_layout(pad=1.4)
    return fig


def sparkline_mpl(years: np.ndarray, values: np.ndarray,
                  color: str = ACCENT, w: float = 2.2, h: float = 0.8) -> plt.Figure:
    """
    Tiny inline sparkline — no axes, no labels, just the trend shape.
    """
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    if len(years) >= 4:
        x_sm, y_sm = _smooth(years.astype(float), values.astype(float), points=80)
    else:
        x_sm, y_sm = years.astype(float), values.astype(float)

    ax.plot(x_sm, y_sm, color=color, linewidth=1.4, solid_capstyle="round")
    ax.fill_between(x_sm, y_sm, alpha=0.18, color=color)
    ax.set_xlim(x_sm.min(), x_sm.max())
    ax.set_ylim(0)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig


def decade_grouped_bar(df_pivot: pd.DataFrame, countries: list[str],
                       title: str = "Patent Output by Decade") -> plt.Figure:
    """
    Grouped bar chart: X = decade, grouped bars = selected countries.
    """
    decade_order = [d for d in ["Pre-1990", "1990s", "2000s", "2010s", "2020s"]
                    if d in df_pivot.columns]
    df_plot = df_pivot.loc[df_pivot.index.isin(countries), decade_order].fillna(0)

    n_groups = len(decade_order)
    n_bars = len(df_plot)
    x = np.arange(n_groups)
    total_width = 0.75
    bar_w = total_width / max(n_bars, 1)
    offsets = np.linspace(-total_width / 2 + bar_w / 2, total_width / 2 - bar_w / 2, n_bars)

    fig, ax = _fig(10, 5)
    for i, (country, offset) in enumerate(zip(df_plot.index, offsets)):
        vals = df_plot.loc[country].values
        c = PALETTE[i % len(PALETTE)]
        bars = ax.bar(x + offset, vals, width=bar_w * 0.88,
                      color=c, edgecolor=BG_CARD, linewidth=0.6,
                      alpha=0.88, zorder=3, label=country)
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.3,
                        f"{int(v)}", ha="center", va="bottom",
                        fontsize=6.5, color=TEXT_2)

    ax.set_xticks(x)
    ax.set_xticklabels(decade_order, fontsize=9)
    ax.set_ylabel("Patents", fontsize=9)
    ax.set_title(title, fontsize=13, fontweight="600", pad=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
    plt.tight_layout(pad=1.4)
    return fig


def growth_comparison_chart(df_yearly: pd.DataFrame, countries: list[str]) -> plt.Figure:
    """
    Side-by-side YoY growth lines for selected countries.
    """
    fig, ax = _fig(10, 5)
    ax.axhline(0, color=TEXT_2, linewidth=1.0, linestyle="-", alpha=0.35)

    for i, country in enumerate(countries):
        sub = df_yearly[df_yearly["country"] == country].sort_values("year").copy()
        if len(sub) < 3:
            continue
        sub["prev"] = sub["patents"].shift(1)
        sub["yoy"] = ((sub["patents"] - sub["prev"]) / sub["prev"] * 100).round(1)
        sub = sub.dropna(subset=["yoy"])
        if sub.empty:
            continue

        c = PALETTE[i % len(PALETTE)]
        x_r = sub["year"].values.astype(float)
        y_r = sub["yoy"].values.astype(float)
        if len(x_r) >= 4:
            x_sm, y_sm = _smooth(x_r, y_r)
        else:
            x_sm, y_sm = x_r, y_r

        ax.fill_between(x_sm, y_sm, alpha=0.07, color=c)
        ax.plot(x_sm, y_sm, color=c, linewidth=2.0,
                label=country, solid_capstyle="round", zorder=4)
        ax.scatter(x_r, y_r, color=c, s=20, zorder=5,
                   edgecolors=BG_PLOT, linewidths=1.1)

    ax.set_title("Year-over-Year Growth Rate Comparison (%)",
                 fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Growth (%)", fontsize=9)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
    plt.tight_layout(pad=1.4)
    return fig


def rank_trajectory_chart(df_yearly: pd.DataFrame, countries: list[str]) -> plt.Figure:
    """
    Rank trajectory — how each country's annual rank changes over time.
    Lower rank = better (rank 1 = most patents that year).
    """
    pivot = (df_yearly.pivot_table(index="year", columns="country",
                                   values="patents", aggfunc="sum")
             .fillna(0))
    rank_pivot = pivot.rank(axis=1, ascending=False, method="min").astype(int)
    max_rank = len(pivot.columns)

    fig, ax = _fig(10, 5)
    ax.set_ylim(max_rank + 0.5, 0.5)   # inverted: rank 1 at top

    for i, country in enumerate(countries):
        if country not in rank_pivot.columns:
            continue
        c = PALETTE[i % len(PALETTE)]
        sub_rank = rank_pivot[country].dropna()
        x_r = sub_rank.index.values.astype(float)
        y_r = sub_rank.values.astype(float)
        if len(x_r) >= 4:
            x_sm, y_sm = _smooth(x_r, y_r)
        else:
            x_sm, y_sm = x_r, y_r

        ax.plot(x_sm, y_sm, color=c, linewidth=2.2, label=country,
                solid_capstyle="round", zorder=4)
        ax.scatter(x_r, y_r, color=c, s=20, zorder=5,
                   edgecolors=BG_PLOT, linewidths=1.1)
        if len(sub_rank) > 0:
            _end_label(ax, x_r[-1], y_r[-1], f"{country[:12]} #{int(y_r[-1])}", c, fontsize=7.5)

    ax.set_title("Country Rank Trajectory (1 = most patents that year)",
                 fontsize=13, fontweight="600", pad=12)
    ax.set_xlabel("Year", fontsize=9)
    ax.set_ylabel("Rank", fontsize=9)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.legend(fontsize=8, loc="lower left", framealpha=0.7)
    plt.tight_layout(pad=1.4)
    return fig


# ================================================================
# SIDEBAR
# ================================================================
st.sidebar.title("Patent Analytics")
st.sidebar.markdown("---")
top_n = st.sidebar.slider("Top N results", 5, 20, 10)
st.sidebar.markdown("---")
st.sidebar.markdown("**Navigation**")
page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Inventors",
        "Companies",
        "Countries",
        "Descriptive Analytics",
        "Predictive Analytics",
        "Data Explorer",
        "Advanced Analysis",
        "Composition Analysis",
        "Comparative Map",        # NEW
    ],
    label_visibility="collapsed",
)

# ================================================================
# PAGE: OVERVIEW
# ================================================================
if page == "Overview":
    st.title("Patent Analytics Dashboard")
    st.markdown("Exploring **PatentsView** granted patent data — descriptive insights and forward-looking forecasts.")

    summary = load_summary()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Patents",       f"{int(summary['total_patents']):,}")
    col2.metric("Total Inventors",     f"{int(summary['total_inventors']):,}")
    col3.metric("Total Companies",     f"{int(summary['total_companies']):,}")
    col4.metric("Total Relationships", f"{int(summary['total_relationships']):,}")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Top Inventors")
        st.pyplot(bar_chart(load_top_inventors(top_n), "inventor", "patents",
                            f"Top {top_n} Inventors", ACCENT))
    with col_b:
        st.subheader("Top Companies")
        st.pyplot(bar_chart(load_top_companies(top_n), "company", "patents",
                            f"Top {top_n} Companies", ACCENT3))

    st.markdown("---")
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Patent Filings by Year")
        st.pyplot(line_chart(load_year_trends(), "year", "patents",
                             "Annual Patent Filings", color=ACCENT))
    with col_d:
        st.subheader("Top Countries")
        st.pyplot(bar_chart(load_top_countries(top_n), "country", "patents",
                            f"Top {top_n} Countries", ACCENT4))

    st.markdown("---")
    st.markdown("### At a Glance — Share Breakdowns")
    ov_c1, ov_c2, ov_c3 = st.columns(3)

    with ov_c1:
        st.subheader("Country Share")
        df_cs = load_country_share_extended(8)
        if not df_cs.empty:
            st.pyplot(donut_chart(
                df_cs["country"].tolist(),
                df_cs["patents"].tolist(),
                "Patents by Country",
                center_label=f"{int(df_cs['patents'].sum()):,}",
                center_sub="total patents",
                figsize=(6, 4.5),
            ))

    with ov_c2:
        st.subheader("Decade Breakdown")
        df_dec = load_decade_share()
        if not df_dec.empty:
            st.pyplot(exploded_pie_chart(
                df_dec["decade"].tolist(),
                df_dec["patents"].tolist(),
                "Patents by Decade",
                highlight_n=1,
                figsize=(6, 4.5),
            ))

    with ov_c3:
        st.subheader("Collaboration Tiers")
        df_col = load_inventor_collaboration_tiers()
        if not df_col.empty:
            st.pyplot(donut_chart(
                df_col["collab_tier"].tolist(),
                df_col["patents"].tolist(),
                "Patents by Team Size",
                center_label="Teams",
                center_sub="per patent",
                figsize=(6, 4.5),
            ))


# ================================================================
# PAGE: INVENTORS
# ================================================================
elif page == "Inventors":
    st.title("Inventors")
    df = load_top_inventors(top_n)
    st.subheader(f"Top {top_n} Inventors by Patent Count")
    st.pyplot(bar_chart(df, "inventor", "patents", f"Top {top_n} Inventors", ACCENT))
    st.subheader("Data Table")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
    st.markdown("---")
    st.subheader("Inventor Rankings (Window Functions)")
    st.dataframe(load_ranked_inventors(top_n), use_container_width=True)
    st.download_button("Download as CSV", data=df.to_csv(index=False),
                       file_name="top_inventors.csv", mime="text/csv")

    st.markdown("---")
    st.markdown("### Inventor Portfolio Distribution")
    inv_c1, inv_c2 = st.columns(2)
    with inv_c1:
        st.subheader("Inventor Tiers by Patent Count")
        st.caption("How many inventors sit in each productivity tier.")
        df_tiers = load_inventor_quartile_distribution()
        if not df_tiers.empty:
            st.pyplot(donut_chart(
                df_tiers["tier"].tolist(),
                df_tiers["inventors"].tolist(),
                "Inventor Tiers",
                center_label=f"{int(df_tiers['inventors'].sum()):,}",
                center_sub="inventors",
                figsize=(7, 5),
            ))
    with inv_c2:
        st.subheader("Productivity Radial Chart")
        st.caption("Each arc represents an inventor tier scaled to their count.")
        if not df_tiers.empty:
            st.pyplot(radial_bar_chart(
                df_tiers["tier"].tolist(),
                df_tiers["inventors"].tolist(),
                "Inventor Count by Tier",
                figsize=(6, 6),
            ))


# ================================================================
# PAGE: COMPANIES
# ================================================================
elif page == "Companies":
    st.title("Companies")
    df = load_top_companies(top_n)
    st.subheader(f"Top {top_n} Companies by Patent Count")
    st.pyplot(bar_chart(df, "company", "patents", f"Top {top_n} Companies", ACCENT3))
    st.subheader("Data Table")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
    st.download_button("Download as CSV", data=df.to_csv(index=False),
                       file_name="top_companies.csv", mime="text/csv")

    st.markdown("---")
    st.markdown("### Company Patent Share")
    comp_c1, comp_c2 = st.columns(2)
    with comp_c1:
        st.subheader("Market Share — Top Companies")
        st.caption("Top companies' share of all patents, with 'Others' as remainder.")
        df_csh = load_company_patent_share(min(top_n, 8))
        if not df_csh.empty:
            st.pyplot(donut_chart(
                df_csh["company"].tolist(),
                df_csh["patents"].tolist(),
                f"Top {min(top_n,8)} Companies + Others",
                center_label=f"{int(df_csh['patents'].sum()):,}",
                center_sub="total patents",
                figsize=(7.5, 5.5),
            ))
    with comp_c2:
        st.subheader("Company Portfolio Size Tiers")
        st.caption("How companies are distributed by the size of their patent portfolio.")
        df_csz = load_company_size_tiers()
        if not df_csz.empty:
            st.pyplot(exploded_pie_chart(
                df_csz["size_tier"].tolist(),
                df_csz["companies"].tolist(),
                "Companies by Portfolio Size",
                highlight_n=1,
                figsize=(7, 5),
            ))

    st.markdown("---")
    st.subheader("Inventor Country Mix — Top Companies")
    st.caption("Each donut shows where a company's inventors come from geographically.")
    n_comp_donuts = st.slider("Companies to show", 3, 6, 4, key="comp_donut_n")
    df_cbd = load_top_company_country_breakdown(n_comp_donuts)
    if not df_cbd.empty:
        groups_data = []
        for company in df_cbd["company"].unique():
            sub = df_cbd[df_cbd["company"] == company].sort_values("patents", ascending=False).head(6)
            groups_data.append((company, sub["country"].tolist(), sub["patents"].tolist()))
        st.pyplot(stacked_donut_small_multiples(groups_data,
                                                 "Country Origin of Inventors — by Company"))


# ================================================================
# PAGE: COUNTRIES
# ================================================================
elif page == "Countries":
    st.title("Countries")
    df = load_top_countries(top_n)
    st.subheader(f"Top {top_n} Countries by Patent Count")
    st.pyplot(bar_chart(df, "country", "patents", f"Top {top_n} Countries", ACCENT4))
    total = df["patents"].sum()
    df["share (%)"] = (df["patents"] / total * 100).round(1)
    st.subheader("Data Table")
    st.dataframe(df.reset_index(drop=True), use_container_width=True)
    st.download_button("Download as CSV", data=df.to_csv(index=False),
                       file_name="country_trends.csv", mime="text/csv")

    st.markdown("---")
    st.markdown("### Country Share Visualisations")
    ctry_c1, ctry_c2 = st.columns(2)
    with ctry_c1:
        st.subheader("Donut — Country Patent Share")
        df_cs2 = load_country_share_extended(min(top_n, 10))
        if not df_cs2.empty:
            st.pyplot(donut_chart(
                df_cs2["country"].tolist(),
                df_cs2["patents"].tolist(),
                "Country Share of Patents",
                center_label=f"{int(df_cs2['patents'].sum()):,}",
                center_sub="patents",
                figsize=(7.5, 5.5),
            ))
    with ctry_c2:
        st.subheader("Radial — Country Output")
        st.caption("Arc length proportional to patent count.")
        if not df_cs2.empty:
            st.pyplot(radial_bar_chart(
                df_cs2["country"].tolist()[:8],
                df_cs2["patents"].tolist()[:8],
                "Patent Output by Country",
                figsize=(6.5, 6.5),
            ))

    st.markdown("---")
    st.subheader("Inventor Density — Patents per Inventor by Country")
    st.caption("Which countries have the highest output per inventor? A proxy for research efficiency.")
    df_dens = load_country_inventor_density()
    if not df_dens.empty:
        fig_dens, ax_dens = _fig(9, 4.5)
        bar_colors_dens = [PIE_PALETTE[i % len(PIE_PALETTE)] for i in range(len(df_dens))]
        bars_dens = ax_dens.bar(df_dens["country"], df_dens["patents_per_inventor"],
                                color=bar_colors_dens, edgecolor=BG_CARD,
                                linewidth=0.8, width=0.65, zorder=3, alpha=0.88)
        for bar in bars_dens:
            h = bar.get_height()
            ax_dens.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                         f"{h:.2f}", ha="center", va="bottom", fontsize=8, color=TEXT_2)
        ax_dens.set_title("Patents per Unique Inventor by Country",
                          fontsize=13, fontweight="600", pad=12)
        ax_dens.set_ylabel("Patents / Inventor", fontsize=9)
        plt.xticks(rotation=35, ha="right", fontsize=8)
        plt.tight_layout(pad=1.4)
        st.pyplot(fig_dens)


# ================================================================
# PAGE: DESCRIPTIVE ANALYTICS
# ================================================================
elif page == "Descriptive Analytics":
    st.title("Descriptive Analytics")
    st.markdown("Historical patterns in patent output — what has happened and where.")

    st.markdown('<span class="section-label label-desc">Descriptive</span>', unsafe_allow_html=True)

    st.subheader("Annual Patent Filings")
    df_yr = load_year_trends()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Filings per Year**")
        st.caption("Raw annual count of granted patents.")
        st.pyplot(line_chart(df_yr, "year", "patents",
                             "Annual Patent Filings", color=ACCENT))
    with col2:
        st.markdown("**Smoothed Trend — Moving Averages**")
        st.caption("3-year and 5-year rolling averages reduce noise.")
        st.pyplot(moving_avg_chart(df_yr, "year", "patents",
                                   "Patent Filings — Moving Averages",
                                   windows=(3, 5), color=ACCENT))

    st.markdown("---")
    n_ctry = st.slider("Countries to compare", 2, 8, 5, key="desc_ctry")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Annual Filings by Country")
        st.caption("Direct comparison of top countries year by year.")
        df_cty = load_patents_per_year_per_country(n_ctry)
        if not df_cty.empty:
            st.pyplot(multi_line_chart(df_cty, "year", "patents", "country",
                                       f"Top {n_ctry} Countries — Annual Filings"))
        else:
            st.warning("No country/year data available.")
    with col4:
        st.subheader("Year-over-Year Growth Rate")
        st.caption("Green = growth, red = decline vs prior year.")
        df_yoy = load_yoy_growth()
        if not df_yoy.empty:
            st.pyplot(growth_bar_chart(df_yoy, "year", "growth_pct",
                                       "Year-over-Year Growth (%)"))
            best = df_yoy.loc[df_yoy["growth_pct"].idxmax()]
            worst = df_yoy.loc[df_yoy["growth_pct"].idxmin()]
            st.success(f"Best growth year: **{int(best['year'])}** (+{best['growth_pct']}%)")
            if worst["growth_pct"] < 0:
                st.error(f"Biggest drop: **{int(worst['year'])}** ({worst['growth_pct']}%)")

    st.markdown("---")
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("Cumulative Patent Race")
        st.caption("Who consistently builds vs who surges late?")
        df_cum = load_cumulative_patents_by_country(limit=5)
        if not df_cum.empty:
            st.pyplot(cumulative_line_chart(df_cum, "year", "cumulative_patents",
                                            "country", "Cumulative Patents by Country"))
        else:
            st.warning("No data.")
    with col6:
        st.subheader("Patent Output by Decade")
        st.caption("Long-run innovation eras at a glance.")
        df_dec = load_patent_age_distribution()
        if not df_dec.empty:
            decade_colors = [ACCENT, ACCENT3, ACCENT2, ACCENT4, "#b06af7"]
            fig, ax = _fig(8, 4.5)
            bars = ax.bar(df_dec["decade"], df_dec["patents"],
                          color=decade_colors[:len(df_dec)],
                          edgecolor=BG_CARD, linewidth=0.8, width=0.6, zorder=3)
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        f"{int(bar.get_height()):,}", ha="center", va="bottom",
                        fontsize=9, color=TEXT_2)
            ax.set_title("Patent Count by Decade", fontsize=13, fontweight="600", pad=12)
            ax.set_ylabel("Patents")
            plt.xticks(fontsize=9)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

    st.markdown("---")
    col7, col8 = st.columns(2)
    with col7:
        st.subheader("Country YoY Growth Lines")
        st.caption("Is each country accelerating or slowing down?")
        df_cyoy = load_country_yoy()
        if not df_cyoy.empty:
            fig, ax = _fig(9, 5)
            ax.axhline(0, color=TEXT_2, linewidth=1.0, linestyle="-", alpha=0.35)
            for i, country in enumerate(df_cyoy["country"].unique()):
                sub = df_cyoy[df_cyoy["country"] == country]
                c = PALETTE[i % len(PALETTE)]
                x_r = sub["year"].values.astype(float)
                y_r = sub["yoy_pct"].values.astype(float)
                x_sm, y_sm = _smooth(x_r, y_r)
                ax.fill_between(x_sm, y_sm, alpha=0.07, color=c)
                ax.plot(x_sm, y_sm, color=c, linewidth=2.0,
                        label=country, solid_capstyle="round")
                ax.scatter(x_r, y_r, color=c, s=18, zorder=5,
                           edgecolors=BG_PLOT, linewidths=1.0)
            ax.set_title("YoY Growth (%) by Country", fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("Growth (%)", fontsize=9)
            ax.legend(fontsize=8)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)
    with col8:
        st.subheader("Top 5 Companies Over Time")
        st.caption("Track how company dominance shifts year by year.")
        df_cy = load_company_yearly_top5()
        if not df_cy.empty:
            st.pyplot(multi_line_chart(df_cy, "year", "patents", "company",
                                       "Top 5 Company Patent Output Over Time"))

    st.markdown("---")
    st.markdown("### Decade-by-Country Composition")
    col9, col10 = st.columns(2)
    with col9:
        st.subheader("Collaboration Structure — Donut")
        st.caption("Proportion of patents filed solo vs collaborative teams.")
        df_collab = load_inventor_collaboration_tiers()
        if not df_collab.empty:
            st.pyplot(donut_chart(
                df_collab["collab_tier"].tolist(),
                df_collab["patents"].tolist(),
                "Patent Collaboration Tiers",
                center_label=f"{int(df_collab['patents'].sum()):,}",
                center_sub="patents",
                figsize=(7, 5),
            ))
    with col10:
        st.subheader("Decade Share — Exploded Pie")
        st.caption("Long-run era breakdown — the fastest-growing decade pops out.")
        df_dec2 = load_decade_share()
        if not df_dec2.empty:
            st.pyplot(exploded_pie_chart(
                df_dec2["decade"].tolist(),
                df_dec2["patents"].tolist(),
                "Patent Output by Decade",
                highlight_n=1,
                figsize=(7, 5),
            ))


# ================================================================
# PAGE: PREDICTIVE ANALYTICS
# ================================================================
elif page == "Predictive Analytics":
    st.title("Predictive Analytics")
    st.markdown("Forward-looking forecasts using linear trend projection on historical data.")

    st.markdown('<span class="section-label label-pred">Predictive</span>', unsafe_allow_html=True)

    forecast_yrs = st.slider("Forecast horizon (years)", 3, 10, 5)

    df_yr = load_year_trends()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Global Patent Forecast")
        st.caption(f"Linear trend extrapolated {forecast_yrs} years beyond last data point. "
                   "Shaded band = +-15% confidence interval.")
        if not df_yr.empty:
            st.pyplot(forecast_line_chart(df_yr, "year", "patents",
                                          "Global Patent Filing Forecast",
                                          forecast_years=forecast_yrs, color=ACCENT))
        else:
            st.warning("No trend data available.")

    with col2:
        st.subheader("Trend vs Smoothed Signal")
        st.caption("5-year moving average removes noise — forecast built on the smoothed signal.")
        if len(df_yr) >= 5:
            df_ma = df_yr.copy()
            df_ma["patents_ma5"] = df_ma["patents"].rolling(5).mean()
            df_ma_clean = df_ma.dropna(subset=["patents_ma5"])
            fig, ax = _fig(9, 5)

            x_raw = df_yr["year"].values.astype(float)
            y_raw = df_yr["patents"].values.astype(float)
            x_sm, y_sm = _smooth(x_raw, y_raw)

            x_ma = df_ma_clean["year"].values.astype(float)
            y_ma = df_ma_clean["patents_ma5"].values.astype(float)
            x_ma_sm, y_ma_sm = _smooth(x_ma, y_ma)

            y_top = max(y_raw.max(), y_ma.max()) * 1.25
            ax.set_ylim(0, y_top)

            ax.fill_between(x_sm, y_sm, alpha=0.05, color=ACCENT)
            ax.plot(x_sm, y_sm, color=ACCENT, linewidth=1.2, alpha=0.4,
                    label="Annual (raw)", solid_capstyle="round")

            _add_gradient_fill(ax, x_ma_sm, y_ma_sm, ACCENT2, alpha_top=0.14, alpha_bottom=0.01)
            ax.plot(x_ma_sm, y_ma_sm, color=ACCENT2, linewidth=2.6,
                    label="5-yr MA", solid_capstyle="round", zorder=5)
            ax.scatter(x_ma, y_ma, color=ACCENT2, s=18, zorder=6,
                       edgecolors=BG_PLOT, linewidths=1.2)

            if len(x_ma) >= 2:
                coeffs = np.polyfit(x_ma, y_ma, 1)
                future_x = np.arange(x_ma[-1] + 1, x_ma[-1] + forecast_yrs + 1)
                forecast_y = np.maximum(np.polyval(coeffs, future_x), 0)

                ax.axvline(x=x_ma[-1], color=TEXT_2, linewidth=0.8,
                           linestyle=":", alpha=0.4)
                ax.text(x_ma[-1] + 0.15, y_top * 0.96, "forecast ->",
                        fontsize=7, color=TEXT_2, alpha=0.55)

                ax.fill_between(future_x, forecast_y * 0.85, forecast_y * 1.15,
                                alpha=0.10, color=ACCENT3)

                bridge_x = np.array([x_ma[-1], future_x[0]])
                bridge_y = np.array([y_ma[-1], forecast_y[0]])
                ax.plot(bridge_x, bridge_y, color=ACCENT3, linewidth=2.0,
                        linestyle="--", alpha=0.8)

                if len(future_x) >= 4:
                    fx_sm, fy_sm = _smooth(future_x, forecast_y)
                    ax.plot(fx_sm, fy_sm, color=ACCENT3, linewidth=2.2,
                            linestyle="--", label="MA Forecast", zorder=6,
                            solid_capstyle="round")
                else:
                    ax.plot(future_x, forecast_y, color=ACCENT3, linewidth=2.2,
                            linestyle="--", label="MA Forecast", zorder=6)

                ax.scatter(future_x, forecast_y, color=ACCENT3, s=40, marker="s",
                           zorder=7, edgecolors=BG_PLOT, linewidths=1.2)

            ax.set_title("Smoothed Trend + Forecast", fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("Patents", fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(max(x,0)):,}"))
            ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)
        else:
            st.warning("Not enough data for 5-yr MA forecast.")

    st.markdown("---")
    st.subheader("Country-Level Patent Forecast")
    st.caption("Each country's historical filings extrapolated forward independently.")
    n_ctry_pred = st.slider("Countries to forecast", 2, 6, 4, key="pred_ctry")
    df_cty = load_patents_per_year_per_country(n_ctry_pred)

    if not df_cty.empty:
        countries = df_cty["country"].unique()
        pairs = [(countries[i], countries[i+1] if i+1 < len(countries) else None)
                 for i in range(0, len(countries), 2)]
        for left_c, right_c in pairs:
            col_l, col_r = st.columns(2)
            for col_widget, ctry in [(col_l, left_c), (col_r, right_c)]:
                if ctry is None:
                    continue
                with col_widget:
                    sub = df_cty[df_cty["country"] == ctry].sort_values("year")
                    st.markdown(f"**{ctry}**")
                    st.pyplot(forecast_line_chart(sub, "year", "patents",
                                                  f"{ctry} — Forecast",
                                                  forecast_years=forecast_yrs,
                                                  color=PALETTE[list(countries).index(ctry) % len(PALETTE)]))
    else:
        st.warning("No country/year data available.")

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Projected Growth Rate Trend")
        st.caption("YoY % growth with trend line — are we accelerating or decelerating?")
        df_yoy = load_yoy_growth()
        if len(df_yoy) >= 3:
            fig, ax = _fig(9, 5)
            ax.bar(df_yoy["year"], df_yoy["growth_pct"],
                   color=[ACCENT2 if v >= 0 else ACCENT4 for v in df_yoy["growth_pct"]],
                   edgecolor=BG_CARD, linewidth=0.6, width=0.7, alpha=0.75, zorder=3)
            ax.axhline(0, color=TEXT_2, linewidth=1.0, linestyle="-", alpha=0.4)
            if len(df_yoy) >= 3:
                x_g = df_yoy["year"].values.astype(float)
                y_g = df_yoy["growth_pct"].values
                coeffs_g = np.polyfit(x_g, y_g, 1)
                x_g_sm, y_g_trend_sm = _smooth(x_g, np.polyval(coeffs_g, x_g))
                ax.plot(x_g_sm, y_g_trend_sm, color=ACCENT3, linewidth=2.0,
                        label="Linear trend", zorder=5, solid_capstyle="round")
                future_xg = np.arange(x_g[-1]+1, x_g[-1]+forecast_yrs+1)
                fy_g = np.polyval(coeffs_g, future_xg)
                ax.plot(future_xg, fy_g, color=ACCENT3, linewidth=1.8,
                        linestyle="--", label="Forecast", zorder=5)
                ax.scatter(future_xg, fy_g, color=ACCENT3, s=30, marker="s",
                           zorder=6, edgecolors=BG_PLOT, linewidths=1.0)
                ax.axvline(x=x_g[-1], color=TEXT_2, linewidth=0.8, linestyle=":", alpha=0.4)
            ax.set_title("YoY Growth Rate + Trend Forecast",
                         fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("Growth (%)", fontsize=9)
            ax.legend(fontsize=8)
            plt.xticks(rotation=35, ha="right", fontsize=8)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)
        else:
            st.warning("Not enough data.")

    with col4:
        st.subheader("Cumulative Forecast by Country")
        st.caption("Projected cumulative totals if current trend continues.")
        df_cum = load_cumulative_patents_by_country(limit=4)
        if not df_cum.empty:
            countries_cum = df_cum["country"].unique()
            fig, ax = _fig(9, 5)
            y_max_c = df_cum["cumulative_patents"].max() * 1.15
            ax.set_ylim(0, y_max_c)

            for i, ctry in enumerate(countries_cum):
                sub = df_cum[df_cum["country"] == ctry].sort_values("year")
                c = PALETTE[i % len(PALETTE)]
                x_c = sub["year"].values.astype(float)
                y_c = sub["cumulative_patents"].values.astype(float)
                x_sm, y_sm = _smooth(x_c, y_c)

                _add_gradient_fill(ax, x_sm, y_sm, c, alpha_top=0.12, alpha_bottom=0.01)
                ax.plot(x_sm, y_sm, color=c, linewidth=2.2, label=ctry,
                        zorder=5, solid_capstyle="round")
                ax.scatter(x_c, y_c, color=c, s=18, zorder=6,
                           edgecolors=BG_PLOT, linewidths=1.2)

                if len(x_c) >= 2:
                    last_growth = y_c[-1] - y_c[-2] if len(y_c) > 1 else 0
                    fx = np.arange(x_c[-1]+1, x_c[-1]+forecast_yrs+1)
                    fy = y_c[-1] + last_growth * np.arange(1, forecast_yrs+1)
                    ax.plot([x_c[-1], fx[0]], [y_c[-1], fy[0]],
                            color=c, linewidth=2.0, linestyle="--", alpha=0.7)
                    ax.plot(fx, fy, color=c, linewidth=1.8, linestyle="--", zorder=4)
                    ax.fill_between(fx, fy*0.9, fy*1.1, alpha=0.05, color=c)
                    ax.scatter(fx, fy, color=c, s=22, marker="s", zorder=5,
                               edgecolors=BG_PLOT, linewidths=1.0)
                    _end_label(ax, x_c[-1], y_c[-1], ctry[:14], c, fontsize=7)

            ax.axvline(x=df_cum["year"].max(), color=TEXT_2,
                       linewidth=0.8, linestyle=":", alpha=0.4)
            ax.set_title("Cumulative Patent Forecast by Country",
                         fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("Cumulative Patents", fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
            ax.legend(fontsize=8, loc="upper left")
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)
        else:
            st.warning("No cumulative data.")

    st.markdown("---")
    st.subheader("Forecast Summary Table")
    st.caption("Projected annual patent filings based on linear regression of historical data.")
    if not df_yr.empty:
        x_all = df_yr["year"].values.astype(float)
        y_all = df_yr["patents"].values.astype(float)
        if len(x_all) >= 2:
            coeffs_all = np.polyfit(x_all, y_all, 1)
            future_years = list(range(int(x_all[-1])+1, int(x_all[-1])+forecast_yrs+1))
            forecast_vals = [max(int(np.polyval(coeffs_all, yr)), 0) for yr in future_years]
            last_actual = int(y_all[-1])
            forecast_df = pd.DataFrame({
                "Year": future_years,
                "Projected Patents": [f"{v:,}" for v in forecast_vals],
                "vs Last Actual": [f"{'+' if v >= last_actual else ''}{((v-last_actual)/last_actual*100):.1f}%"
                                   for v in forecast_vals],
            })
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)


# ================================================================
# PAGE: DATA EXPLORER
# ================================================================
elif page == "Data Explorer":
    st.title("Data Explorer")
    st.markdown("Browse the joined patents + inventors + companies table.")
    df = load_join_sample(limit=200)
    col1, col2 = st.columns(2)
    with col1:
        country_filter = st.multiselect("Filter by country",
                                        options=sorted(df["country"].dropna().unique()))
    with col2:
        year_filter = st.multiselect("Filter by year",
                                     options=sorted(df["year"].dropna().unique()))
    search = st.text_input("Search by inventor or company name")
    filtered = df.copy()
    if country_filter:
        filtered = filtered[filtered["country"].isin(country_filter)]
    if year_filter:
        filtered = filtered[filtered["year"].isin(year_filter)]
    if search:
        mask = (filtered["inventor"].str.contains(search, case=False, na=False)
                | filtered["company"].str.contains(search, case=False, na=False))
        filtered = filtered[mask]
    st.markdown(f"Showing **{len(filtered):,}** records")
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)
    st.download_button("Download filtered data", data=filtered.to_csv(index=False),
                       file_name="patent_explorer.csv", mime="text/csv")


# ================================================================
# PAGE: ADVANCED ANALYSIS
# ================================================================
elif page == "Advanced Analysis":
    st.title("Advanced Analysis")
    st.markdown(
        "Deep-dive into patent patterns, productivity, geographic dominance, "
        "and structural innovation trends."
    )

    with st.expander("Page filters", expanded=False):
        fa_col1, fa_col2, fa_col3 = st.columns(3)
        with fa_col1:
            adv_top_n = st.slider("Top-N companies / countries", 4, 12, 6, key="adv_topn")
        with fa_col2:
            adv_min_patents = st.slider("Min patents threshold", 1, 10, 2, key="adv_minp")
        with fa_col3:
            adv_countries = st.slider("Countries in multi-country charts", 3, 8, 5, key="adv_ctry")

    st.markdown("---")

    st.markdown("### Growth & Share")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Year-over-Year Growth")
        st.caption(
            "Each lollipop length = magnitude, colour = direction. "
            "Dashed line = long-run average; callouts flag outlier years."
        )
        df_yoy = load_yoy_growth()
        if df_yoy.empty:
            st.warning("Not enough data.")
        else:
            fig, ax = _fig(9, 5)
            avg_g = df_yoy["growth_pct"].mean()
            colors_lol = [ACCENT2 if v >= 0 else ACCENT4 for v in df_yoy["growth_pct"]]

            for _, row in df_yoy.iterrows():
                ax.vlines(row["year"], 0, row["growth_pct"],
                          color=ACCENT2 if row["growth_pct"] >= 0 else ACCENT4,
                          linewidth=2.2, alpha=0.7, zorder=3)
            ax.scatter(df_yoy["year"], df_yoy["growth_pct"],
                       color=colors_lol, s=60, zorder=5,
                       edgecolors=BG_PLOT, linewidths=1.6)
            ax.axhline(0, color=TEXT_1, linewidth=1.0, alpha=0.5, zorder=4)
            ax.axhline(avg_g, color=ACCENT3, linewidth=1.4,
                       linestyle="--", alpha=0.75, zorder=4,
                       label=f"Avg {avg_g:+.1f}%")

            top2 = df_yoy.nlargest(2, "growth_pct")
            bot2 = df_yoy.nsmallest(2, "growth_pct")
            for _, row in pd.concat([top2, bot2]).iterrows():
                sign = "+" if row["growth_pct"] >= 0 else ""
                offset = (0, 9) if row["growth_pct"] >= 0 else (0, -14)
                ax.annotate(
                    f"{sign}{row['growth_pct']:.1f}%",
                    xy=(row["year"], row["growth_pct"]),
                    xytext=offset, textcoords="offset points",
                    fontsize=7.5, fontweight="700",
                    color=ACCENT2 if row["growth_pct"] >= 0 else ACCENT4,
                    ha="center",
                    path_effects=[pe.withStroke(linewidth=2.5, foreground=BG_PLOT)],
                )

            ax.set_title("YoY Patent Growth — Diverging Lollipop",
                         fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("Growth (%)", fontsize=9)
            ax.legend(fontsize=8, framealpha=0.6)
            plt.xticks(rotation=35, ha="right", fontsize=8)
            ax.axhspan(0, df_yoy["growth_pct"].max() * 1.4,
                       alpha=0.03, color=ACCENT2, zorder=1)
            ax.axhspan(df_yoy["growth_pct"].min() * 1.4, 0,
                       alpha=0.03, color=ACCENT4, zorder=1)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

            best = df_yoy.loc[df_yoy["growth_pct"].idxmax()]
            worst = df_yoy.loc[df_yoy["growth_pct"].idxmin()]
            m1, m2, m3 = st.columns(3)
            m1.metric("Best Year", int(best["year"]), delta=f"+{best['growth_pct']:.1f}%")
            m2.metric("Worst Year", int(worst["year"]), delta=f"{worst['growth_pct']:.1f}%")
            m3.metric("Long-run Avg", f"{avg_g:+.1f}%/yr")

    with col2:
        st.subheader("Country Share Over Time")
        st.caption(
            "Stacked area shows composition, not just volume. "
            "Widening bands = growing share; narrowing = losing ground."
        )
        df_cty_yr = load_patents_per_year_per_country(adv_countries)
        if df_cty_yr.empty:
            st.warning("No country/year data.")
        else:
            pivot_share = (
                df_cty_yr.pivot_table(index="year", columns="country",
                                      values="patents", aggfunc="sum")
                .fillna(0)
            )
            pivot_pct = pivot_share.div(pivot_share.sum(axis=1), axis=0) * 100
            countries_s = pivot_pct.columns.tolist()

            fig, ax = _fig(9, 5)
            y_bottom = np.zeros(len(pivot_pct))

            for i, ctry in enumerate(countries_s):
                c = PALETTE[i % len(PALETTE)]
                vals = pivot_pct[ctry].values
                ax.fill_between(pivot_pct.index, y_bottom, y_bottom + vals,
                                alpha=0.82, color=c, label=ctry, zorder=3)
                mid = y_bottom[-1] + vals[-1] / 2
                if vals[-1] > 4:
                    ax.text(pivot_pct.index[-1] + 0.3, mid,
                            f"{ctry[:10]} {vals[-1]:.0f}%",
                            fontsize=7, color=TEXT_1, va="center", fontweight="600",
                            path_effects=[pe.withStroke(linewidth=2, foreground=BG_CARD)])
                y_bottom += vals

            ax.set_xlim(pivot_pct.index.min(), pivot_pct.index.max() + 2)
            ax.set_ylim(0, 100)
            ax.set_title("Patent Share by Country — Stacked Area (%)",
                         fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("Share (%)", fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
            ax.legend(fontsize=7.5, loc="upper left", framealpha=0.6,
                      ncol=2 if len(countries_s) > 4 else 1)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

    st.markdown("---")

    st.markdown("### Inventor Insights")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Inventor Productivity Distribution")
        st.caption(
            "How patents are distributed across inventors. "
            "The long tail reveals a superstar effect."
        )
        df_prod = load_inventor_productivity()
        if df_prod.empty:
            st.warning("No data.")
        else:
            max_bucket = 8
            df_prod["bucket"] = df_prod["patent_count"].clip(upper=max_bucket)
            bucketed = (
                df_prod.groupby("bucket")["num_inventors"]
                .sum()
                .reset_index()
            )

            fig, ax = _fig(8, 4.8)
            total_inv = bucketed["num_inventors"].sum()

            norm_col = Normalize(vmin=0, vmax=bucketed["num_inventors"].max())
            cmap_col = plt.cm.get_cmap("YlOrRd")

            for _, row in bucketed.iterrows():
                c = cmap_col(norm_col(row["num_inventors"]))
                ax.bar(row["bucket"], row["num_inventors"],
                       color=c, edgecolor=BG_CARD,
                       linewidth=0.8, width=0.7, zorder=3, alpha=0.9)

            for _, row in bucketed.iterrows():
                pct = row["num_inventors"] / total_inv * 100
                ax.text(row["bucket"], row["num_inventors"] + total_inv * 0.005,
                        f"{pct:.1f}%", ha="center", va="bottom",
                        fontsize=8, color=TEXT_2, fontweight="600")

            cumsum = 0
            median_bucket = bucketed["bucket"].iloc[-1]
            for _, row in bucketed.iterrows():
                cumsum += row["num_inventors"]
                if cumsum >= total_inv / 2:
                    median_bucket = row["bucket"]
                    break
            ax.axvline(median_bucket, color=ACCENT, linewidth=1.8,
                       linestyle="--", alpha=0.7, label=f"Median ~{int(median_bucket)} patent(s)")

            ax.axvspan(max_bucket - 0.5, max_bucket + 0.5,
                       alpha=0.08, color=ACCENT3, zorder=2)
            ax.text(max_bucket, bucketed["num_inventors"].max() * 0.92,
                    f"{max_bucket}+\nsuperstars",
                    fontsize=7, color=ACCENT3, ha="center", style="italic")

            xtick_labels = [str(int(b)) if b < max_bucket else f"{max_bucket}+"
                            for b in bucketed["bucket"]]
            ax.set_xticks(bucketed["bucket"])
            ax.set_xticklabels(xtick_labels, fontsize=9)
            ax.set_title("Patents per Inventor — Distribution",
                         fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Number of Patents Held", fontsize=9)
            ax.set_ylabel("Number of Inventors", fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
            ax.legend(fontsize=8, framealpha=0.6)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

            solo = int(bucketed.loc[bucketed["bucket"] == 1, "num_inventors"].sum())
            st.info(
                f"**{solo:,}** inventors ({solo/total_inv*100:.0f}%) hold exactly 1 patent. "
                f"The {max_bucket}+ bucket represents the productive elite."
            )

    with col4:
        st.subheader("Collaboration Intensity by Company")
        st.caption(
            "Dot-plot of avg inventors per patent. "
            "Above benchmark = collaborative; below = concentrated IP."
        )
        df_ratio = load_company_inventor_ratio()
        if df_ratio.empty:
            st.warning("No data.")
        else:
            df_r = df_ratio.sort_values("inventors_per_patent").reset_index(drop=True)
            benchmark = df_r["inventors_per_patent"].median()

            fig, ax = _fig(8, max(4.5, len(df_r) * 0.42))
            y_pos = range(len(df_r))

            ax.axvline(benchmark, color=ACCENT3, linewidth=1.4,
                       linestyle="--", alpha=0.7, zorder=3,
                       label=f"Median {benchmark:.2f}")

            for i, row in df_r.iterrows():
                c = ACCENT2 if row["inventors_per_patent"] >= benchmark else ACCENT4
                ax.hlines(i, benchmark, row["inventors_per_patent"],
                          color=c, linewidth=1.8, alpha=0.5, zorder=3)
                ax.scatter(row["inventors_per_patent"], i,
                           color=c, s=70, zorder=5,
                           edgecolors=BG_PLOT, linewidths=1.5)
                offset = 0.04 if row["inventors_per_patent"] >= benchmark else -0.04
                ha = "left" if offset > 0 else "right"
                ax.text(row["inventors_per_patent"] + offset, i,
                        f"{row['inventors_per_patent']:.2f}",
                        va="center", ha=ha, fontsize=7.5, color=TEXT_2)

            ax.set_yticks(y_pos)
            ax.set_yticklabels([n[:22] for n in df_r["company"]], fontsize=8)
            ax.set_xlabel("Avg Inventors per Patent", fontsize=9)
            ax.set_title("Collaboration Intensity — Dot Plot",
                         fontsize=13, fontweight="600", pad=12)
            ax.legend(fontsize=8, framealpha=0.6)

            x_max = df_r["inventors_per_patent"].max() * 1.15
            ax.axvspan(benchmark, x_max, alpha=0.04, color=ACCENT2, zorder=1)
            ax.axvspan(0, benchmark, alpha=0.04, color=ACCENT4, zorder=1)
            ax.set_xlim(0, x_max)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

    st.markdown("---")

    st.markdown("### Geographic Patterns")
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Patent Volume by Country (Stacked)")
        df_cty_yr2 = load_patents_per_year_per_country(adv_countries)
        if df_cty_yr2.empty:
            st.warning("No data.")
        else:
            pivot_abs = (
                df_cty_yr2.pivot_table(index="year", columns="country",
                                       values="patents", aggfunc="sum")
                .fillna(0)
            )
            countries_a = pivot_abs.columns.tolist()
            fig, ax = _fig(9, 5)
            y_bottom = np.zeros(len(pivot_abs))

            for i, ctry in enumerate(countries_a):
                c = PALETTE[i % len(PALETTE)]
                vals = pivot_abs[ctry].values
                x_sm, y_bot_sm = _smooth(pivot_abs.index.astype(float), y_bottom)
                x_sm, y_top_sm = _smooth(pivot_abs.index.astype(float), y_bottom + vals)
                ax.fill_between(x_sm, y_bot_sm, y_top_sm,
                                alpha=0.8, color=c, label=ctry, zorder=3)
                ax.plot(x_sm, y_top_sm, color=c, linewidth=0.8, alpha=0.6, zorder=4)
                mid = (y_bottom[-1] + (y_bottom[-1] + vals[-1])) / 2
                if vals[-1] > pivot_abs.values.max() * 0.04:
                    ax.text(pivot_abs.index[-1] + 0.3, mid,
                            ctry[:10], fontsize=7, color=TEXT_1,
                            va="center", fontweight="600",
                            path_effects=[pe.withStroke(linewidth=2, foreground=BG_CARD)])
                y_bottom += vals

            ax.set_xlim(pivot_abs.index.min(), pivot_abs.index.max() + 2)
            ax.set_ylim(0)
            ax.set_title("Absolute Patent Volume — Stacked Area",
                         fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("Patents", fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
            ax.legend(fontsize=7.5, loc="upper left", framealpha=0.6,
                      ncol=2 if len(countries_a) > 4 else 1)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

    with col6:
        st.subheader("Country x Company Heatmap")
        df_cc = load_country_company_matrix(
            top_n_countries=min(adv_top_n, 8),
            top_n_companies=min(adv_top_n, 8)
        )
        if df_cc.empty:
            st.warning("No data.")
        else:
            pivot_cc = df_cc.pivot_table(
                index="country", columns="company",
                values="patents", fill_value=0
            )
            row_max = pivot_cc.max(axis=1)
            pivot_norm = pivot_cc.div(row_max, axis=0)

            fig, ax = plt.subplots(
                figsize=(max(9, len(pivot_cc.columns) * 1.2),
                         max(4, len(pivot_cc.index) * 0.75))
            )
            fig.patch.set_facecolor(BG_CARD)
            ax.set_facecolor(BG_CARD)

            im = ax.imshow(pivot_norm.values, cmap="YlOrRd",
                           aspect="auto", vmin=0, vmax=1)

            ax.set_xticks(range(len(pivot_cc.columns)))
            ax.set_xticklabels([c[:18] for c in pivot_cc.columns],
                               rotation=38, ha="right", fontsize=8)
            ax.set_yticks(range(len(pivot_cc.index)))
            ax.set_yticklabels(pivot_cc.index, fontsize=9)

            flat = pivot_cc.values.flatten()
            top3_thresh = sorted(flat[flat > 0], reverse=True)[:3]
            for i in range(len(pivot_cc.index)):
                for j in range(len(pivot_cc.columns)):
                    raw = pivot_cc.values[i, j]
                    if raw == 0:
                        continue
                    nrm = pivot_norm.values[i, j]
                    tc = "white" if nrm > 0.55 else TEXT_1
                    weight = "bold" if raw in top3_thresh else "normal"
                    ax.text(j, i, f"{int(raw)}",
                            ha="center", va="center",
                            fontsize=8, color=tc, fontweight=weight)
                    if raw in top3_thresh:
                        rect = mpatches.FancyBboxPatch(
                            (j - 0.48, i - 0.48), 0.96, 0.96,
                            linewidth=1.8, edgecolor=ACCENT3,
                            facecolor="none", zorder=5,
                            boxstyle="round,pad=0"
                        )
                        ax.add_patch(rect)

            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label("Relative intensity (row-normalised)", fontsize=8, color=TEXT_2)
            cbar.ax.yaxis.set_tick_params(color=TEXT_2, labelsize=7)
            ax.set_title("Patent Count: Country vs Company (row-normalised)",
                         fontsize=12, fontweight="600", pad=10, color=TEXT_1)
            plt.tight_layout()
            st.pyplot(fig)

    st.markdown("---")

    st.markdown("### Rankings & Efficiency")
    col7, col8 = st.columns(2)

    with col7:
        st.subheader("Country Rank Change (Slope Chart)")
        df_cty_yr3 = load_patents_per_year_per_country(adv_countries + 2)
        if df_cty_yr3.empty:
            st.warning("No data.")
        else:
            pivot_rank = (
                df_cty_yr3.pivot_table(index="year", columns="country",
                                       values="patents", aggfunc="sum")
                .fillna(0)
            )
            first_year = pivot_rank.index.min()
            last_year = pivot_rank.index.max()
            rank_first = pivot_rank.loc[first_year].rank(ascending=False).astype(int)
            rank_last = pivot_rank.loc[last_year].rank(ascending=False).astype(int)

            fig, ax = _fig(7, 5)
            ax.set_xlim(-0.5, 1.5)
            ax.set_ylim(0.5, len(rank_first) + 0.5)
            ax.invert_yaxis()
            ax.set_xticks([0, 1])
            ax.set_xticklabels([str(int(first_year)), str(int(last_year))],
                               fontsize=11, fontweight="600", color=TEXT_1)
            ax.yaxis.set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.grid(False)

            for i, ctry in enumerate(rank_first.index):
                r1 = rank_first[ctry]
                r2 = rank_last[ctry]
                delta = r1 - r2
                c = ACCENT2 if delta > 0 else (ACCENT4 if delta < 0 else TEXT_2)

                ax.plot([0, 1], [r1, r2], color=c, linewidth=2.2, alpha=0.8,
                        zorder=3, solid_capstyle="round")
                ax.scatter([0, 1], [r1, r2], color=c, s=55, zorder=4,
                           edgecolors=BG_PLOT, linewidths=1.4)

                ax.text(-0.07, r1, f"#{r1} {ctry[:12]}",
                        ha="right", va="center", fontsize=8,
                        color=TEXT_1, fontweight="500")
                arrow = "up" if delta > 0 else ("down" if delta < 0 else "-")
                ax.text(1.07, r2, f"{ctry[:12]} #{r2} ({arrow})",
                        ha="left", va="center", fontsize=8,
                        color=c, fontweight="600")

            ax.set_title(f"Country Rankings: {int(first_year)} vs {int(last_year)}",
                         fontsize=13, fontweight="600", pad=12)
            leg_patches = [
                mpatches.Patch(color=ACCENT2, label="Climbed"),
                mpatches.Patch(color=ACCENT4, label="Fell"),
                mpatches.Patch(color=TEXT_2,  label="Stable"),
            ]
            ax.legend(handles=leg_patches, fontsize=8, loc="lower right", framealpha=0.6)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

    with col8:
        st.subheader("Efficiency Quadrant — Team Size vs Output")
        df_eff = load_inventor_efficiency()
        if df_eff.empty:
            st.warning("No data.")
        else:
            med_inv = df_eff["inventors"].median()
            med_pat = df_eff["patents"].median()

            fig, ax = _fig(9, 5.2)
            ax.set_xlim(0, df_eff["inventors"].max() * 1.2)
            ax.set_ylim(0, df_eff["patents"].max() * 1.2)

            quadrant_cfg = [
                (med_inv, df_eff["inventors"].max()*1.2, med_pat, df_eff["patents"].max()*1.2,
                 ACCENT2, "Stars"),
                (0, med_inv, med_pat, df_eff["patents"].max()*1.2,
                 ACCENT3, "Lean\nMachines"),
                (med_inv, df_eff["inventors"].max()*1.2, 0, med_pat,
                 ACCENT4, "Laggards"),
                (0, med_inv, 0, med_pat,
                 TEXT_2, "Niche"),
            ]
            for x0, x1, y0, y1, c, label in quadrant_cfg:
                ax.fill_between([x0, x1], [y0, y0], [y1, y1],
                                alpha=0.06, color=c, zorder=1)
                ax.text((x0+x1)/2, (y0+y1)/2, label,
                        ha="center", va="center", fontsize=8,
                        color=c, alpha=0.55, fontweight="700",
                        style="italic")

            ax.axvline(med_inv, color=TEXT_2, linewidth=0.9,
                       linestyle=":", alpha=0.5, zorder=2)
            ax.axhline(med_pat, color=TEXT_2, linewidth=0.9,
                       linestyle=":", alpha=0.5, zorder=2)

            norm_eff = Normalize(
                vmin=df_eff["patents_per_inventor"].min(),
                vmax=df_eff["patents_per_inventor"].max()
            )
            bubble_s = (df_eff["patents_per_inventor"] * 100).clip(lower=40)
            sc = ax.scatter(
                df_eff["inventors"], df_eff["patents"],
                s=bubble_s, alpha=0.82,
                c=df_eff["patents_per_inventor"],
                cmap="YlOrRd",
                edgecolors=BORDER_C, linewidths=0.9, zorder=4
            )

            for _, row in df_eff.iterrows():
                ax.annotate(
                    row["company"][:15],
                    (row["inventors"], row["patents"]),
                    fontsize=6.8, ha="center", va="bottom",
                    xytext=(0, 6), textcoords="offset points",
                    color=TEXT_2,
                    path_effects=[pe.withStroke(linewidth=2, foreground=BG_PLOT)]
                )

            cbar = plt.colorbar(sc, ax=ax, shrink=0.75)
            cbar.set_label("Patents / Inventor", fontsize=8, color=TEXT_2)
            cbar.ax.yaxis.set_tick_params(color=TEXT_2, labelsize=7)
            ax.set_xlabel("Unique Inventors", fontsize=9)
            ax.set_ylabel("Total Patents", fontsize=9)
            ax.set_title("Efficiency Quadrant — Team Size vs Output",
                         fontsize=13, fontweight="600", pad=12)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

    st.markdown("---")

    st.markdown("### Structural Innovation Metrics")
    col9, col10 = st.columns(2)

    with col9:
        st.subheader("Innovation Concentration Index (HHI)")
        df_cy_hhi = load_company_yearly_top5()
        if not df_cy_hhi.empty:
            def compute_hhi(group):
                total = group["patents"].sum()
                if total == 0:
                    return 0
                shares = group["patents"] / total
                return (shares ** 2).sum() * 10000

            hhi_by_year = (
                df_cy_hhi.groupby("year")
                .apply(compute_hhi)
                .reset_index()
                .rename(columns={0: "hhi"})
            )
            hhi_by_year = hhi_by_year[hhi_by_year["hhi"] > 0]

            fig, ax = _fig(9, 5)
            x_raw = hhi_by_year["year"].values.astype(float)
            y_raw = hhi_by_year["hhi"].values.astype(float)
            x_sm, y_sm = _smooth(x_raw, y_raw)

            ax.axhspan(2500, 10000, alpha=0.06, color=ACCENT4, zorder=1)
            ax.axhspan(1500, 2500, alpha=0.05, color=ACCENT3, zorder=1)
            ax.axhspan(0,    1500, alpha=0.05, color=ACCENT2, zorder=1)

            x_label = x_raw.max() + 0.2
            for y_pos, label, c in [(6000, "Highly\nConcentrated", ACCENT4),
                                     (2000, "Moderate", ACCENT3),
                                     (750,  "Competitive", ACCENT2)]:
                ax.text(x_label, y_pos, label,
                        fontsize=7, color=c, va="center", alpha=0.7, fontweight="600")

            _add_gradient_fill(ax, x_sm, y_sm, ACCENT, alpha_top=0.18, alpha_bottom=0.01)
            ax.plot(x_sm, y_sm, color=ACCENT, linewidth=2.6, zorder=5,
                    solid_capstyle="round", label="HHI")
            ax.scatter(x_raw, y_raw, color=ACCENT, s=30, zorder=6,
                       edgecolors=BG_PLOT, linewidths=1.4)

            peak_idx = np.argmax(y_raw)
            ax.annotate(
                f"Peak\n{int(y_raw[peak_idx]):,}",
                xy=(x_raw[peak_idx], y_raw[peak_idx]),
                xytext=(0, 14), textcoords="offset points",
                ha="center", fontsize=8, color=ACCENT4, fontweight="700",
                arrowprops=dict(arrowstyle="-|>", color=ACCENT4, lw=1.2),
                path_effects=[pe.withStroke(linewidth=2.5, foreground=BG_PLOT)]
            )

            ax.set_xlim(x_raw.min() - 0.5, x_raw.max() + 2.5)
            ax.set_ylim(0, 10500)
            ax.set_title("Innovation Concentration Index (HHI) Over Time",
                         fontsize=13, fontweight="600", pad=12)
            ax.set_xlabel("Year", fontsize=9)
            ax.set_ylabel("HHI Score (0 to 10,000)", fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
            ax.legend(fontsize=8, framealpha=0.6)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

            latest_hhi = int(y_raw[-1])
            zone = ("Highly Concentrated" if latest_hhi > 2500
                    else "Moderately Concentrated" if latest_hhi > 1500
                    else "Competitive")
            st.info(f"Latest HHI: **{latest_hhi:,}** — market is **{zone}**.")
        else:
            st.warning("No company/year data.")

    with col10:
        st.subheader("Company Geographic Diversity")
        df_div = load_company_country_diversity()
        if df_div.empty:
            st.warning("No data.")
        else:
            fig, ax = _fig(9, 5.2)
            df_div["eff"] = df_div["total_patents"] / df_div["countries_represented"]

            sc2 = ax.scatter(
                df_div["countries_represented"],
                df_div["total_patents"],
                s=(df_div["total_inventors"] * 8).clip(lower=40),
                c=df_div["eff"], cmap="plasma",
                alpha=0.85, edgecolors=BORDER_C, linewidths=0.9,
                zorder=4
            )

            for _, row in df_div.iterrows():
                ax.annotate(
                    row["company"][:16],
                    (row["countries_represented"], row["total_patents"]),
                    fontsize=6.8, ha="center", va="bottom",
                    xytext=(0, 6), textcoords="offset points",
                    color=TEXT_2,
                    path_effects=[pe.withStroke(linewidth=2, foreground=BG_PLOT)]
                )

            med_c = df_div["countries_represented"].median()
            med_p2 = df_div["total_patents"].median()
            ax.axvline(med_c, color=TEXT_2, linewidth=0.9, linestyle=":", alpha=0.45, zorder=2)
            ax.axhline(med_p2, color=TEXT_2, linewidth=0.9, linestyle=":", alpha=0.45, zorder=2)

            cbar2 = plt.colorbar(sc2, ax=ax, shrink=0.75)
            cbar2.set_label("Patents per Country (efficiency)", fontsize=8, color=TEXT_2)
            cbar2.ax.yaxis.set_tick_params(color=TEXT_2, labelsize=7)
            ax.set_xlabel("Countries Represented", fontsize=9)
            ax.set_ylabel("Total Patents", fontsize=9)
            ax.set_title("Geographic Diversity vs Patent Volume\n(bubble = inventor count)",
                         fontsize=13, fontweight="600", pad=12)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig)

    st.markdown("---")

    st.markdown("### Inventor x Country Cross-Analysis")
    st.subheader("Top Inventors by Country Origin — Heatmap")
    df_ich = load_inventor_country_heatmap(top_n_countries=6, top_n_inventors=10)
    if not df_ich.empty:
        pivot_ich = df_ich.pivot_table(
            index="inventor", columns="country", values="patents", fill_value=0
        )
        col_max = pivot_ich.max(axis=0)
        pivot_ich_norm = pivot_ich.div(col_max, axis=1).fillna(0)

        fig, ax = plt.subplots(
            figsize=(max(10, len(pivot_ich.columns) * 1.5),
                     max(5, len(pivot_ich.index) * 0.62))
        )
        fig.patch.set_facecolor(BG_CARD)
        ax.set_facecolor(BG_CARD)
        im3 = ax.imshow(pivot_ich_norm.values, cmap="Oranges",
                        aspect="auto", vmin=0, vmax=1)

        ax.set_xticks(range(len(pivot_ich.columns)))
        ax.set_xticklabels(pivot_ich.columns, fontsize=10, fontweight="600")
        ax.set_yticks(range(len(pivot_ich.index)))
        ax.set_yticklabels([n[:28] for n in pivot_ich.index], fontsize=8.5)

        for i in range(len(pivot_ich.index)):
            for j in range(len(pivot_ich.columns)):
                raw = pivot_ich.values[i, j]
                nrm = pivot_ich_norm.values[i, j]
                if raw == 0:
                    continue
                tc = "white" if nrm > 0.55 else "#1a1a1a"
                weight = "bold" if nrm == 1.0 else "normal"
                ax.text(j, i, str(int(raw)),
                        ha="center", va="center",
                        fontsize=9, color=tc, fontweight=weight)

        cbar3 = plt.colorbar(im3, ax=ax, shrink=0.7)
        cbar3.set_label("Relative output (column-normalised)", fontsize=8, color=TEXT_2)
        cbar3.ax.yaxis.set_tick_params(color=TEXT_2, labelsize=7)
        ax.set_title("Top Inventors x Country — Column-Normalised Heatmap",
                     fontsize=13, fontweight="600", pad=12, color=TEXT_1)
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("---")

    st.markdown("### Key Metrics at a Glance")
    df_yoy2   = load_yoy_growth()
    df_prod2  = load_inventor_productivity()
    df_sh2    = load_country_share()
    df_div2   = load_company_country_diversity()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        if not df_sh2.empty:
            top_c = df_sh2.iloc[0]
            total_sh = df_sh2["patents"].sum()
            st.metric("Leading Country", top_c["country"],
                      delta=f"{top_c['patents']/total_sh*100:.1f}% share")
    with kpi2:
        if not df_prod2.empty:
            single = df_prod2[df_prod2["patent_count"] == 1]["num_inventors"].sum()
            total_i = df_prod2["num_inventors"].sum()
            st.metric("Single-patent Inventors",
                      f"{int(single):,}",
                      delta=f"{single/total_i*100:.0f}% of all inventors")
    with kpi3:
        if not df_yoy2.empty:
            avg_g2 = df_yoy2["growth_pct"].mean()
            st.metric("Avg Annual Growth", f"{avg_g2:+.1f}%",
                      delta="long-run trend")
    with kpi4:
        if not df_div2.empty:
            most_global = df_div2.iloc[0]
            st.metric("Most Global Company",
                      most_global["company"][:18],
                      delta=f"{int(most_global['countries_represented'])} countries")


# ================================================================
# PAGE: COMPOSITION ANALYSIS
# ================================================================
elif page == "Composition Analysis":
    st.title("Composition Analysis")
    st.markdown(
        "Pie, donut, and radial charts revealing how patents are distributed "
        "across companies, countries, decades, and collaboration structures."
    )

    st.markdown("### Geographic & Temporal Composition")
    c1a, c1b, c1c = st.columns(3)

    with c1a:
        st.subheader("Country Share — Donut")
        st.caption("Inner label = total patents in dataset.")
        n_ctry_comp = st.slider("Countries", 4, 12, 8, key="comp_ctry")
        df_cs = load_country_share_extended(n_ctry_comp)
        if not df_cs.empty:
            st.pyplot(donut_chart(
                df_cs["country"].tolist(),
                df_cs["patents"].tolist(),
                "Patent Share by Country",
                center_label=f"{int(df_cs['patents'].sum()):,}",
                center_sub="patents total",
                figsize=(7, 5.5),
            ))

    with c1b:
        st.subheader("Decade Share — Exploded Pie")
        st.caption("Dominant decade is exploded outward for emphasis.")
        df_dec = load_decade_share()
        if not df_dec.empty:
            st.pyplot(exploded_pie_chart(
                df_dec["decade"].tolist(),
                df_dec["patents"].tolist(),
                "Patents by Decade",
                highlight_n=1,
                figsize=(7, 5.5),
            ))

    with c1c:
        st.subheader("Country Radial Chart")
        st.caption("Arc length proportional to patent count — a different lens on share.")
        if not df_cs.empty:
            st.pyplot(radial_bar_chart(
                df_cs["country"].tolist()[:9],
                df_cs["patents"].tolist()[:9],
                "Patent Output by Country",
                figsize=(6.5, 6.5),
            ))

    st.markdown("---")

    st.markdown("### Company Portfolio Composition")
    c2a, c2b = st.columns(2)

    with c2a:
        st.subheader("Top Companies + Others — Donut")
        n_comp_share = st.slider("Top companies", 4, 12, 7, key="comp_share_n")
        df_csh = load_company_patent_share(n_comp_share)
        if not df_csh.empty:
            top_pct = df_csh[df_csh["company"] != "Others"]["share"].sum()
            st.pyplot(donut_chart(
                df_csh["company"].tolist(),
                df_csh["patents"].tolist(),
                f"Top {n_comp_share} Companies vs Rest",
                center_label=f"{top_pct:.0f}%",
                center_sub=f"top-{n_comp_share} share",
                figsize=(8, 6),
            ))

    with c2b:
        st.subheader("Company Portfolio Size Distribution")
        df_csz = load_company_size_tiers()
        if not df_csz.empty:
            col_order = ["1 patent", "2-5 patents", "6-20 patents", "20+ patents"]
            df_csz["size_tier"] = pd.Categorical(df_csz["size_tier"],
                                                  categories=col_order, ordered=True)
            df_csz = df_csz.sort_values("size_tier")
            st.pyplot(donut_chart(
                df_csz["size_tier"].tolist(),
                df_csz["companies"].tolist(),
                "Companies by Portfolio Size",
                colors=[ACCENT4, ACCENT3, ACCENT, ACCENT2],
                center_label=f"{int(df_csz['companies'].sum()):,}",
                center_sub="companies",
                figsize=(7.5, 5.5),
            ))

    st.markdown("---")

    st.markdown("### Innovation Structure")
    c3a, c3b, c3c = st.columns(3)

    with c3a:
        st.subheader("Collaboration Tiers")
        df_collab = load_inventor_collaboration_tiers()
        if not df_collab.empty:
            st.pyplot(donut_chart(
                df_collab["collab_tier"].tolist(),
                df_collab["patents"].tolist(),
                "Team Size per Patent",
                colors=[ACCENT2, ACCENT, ACCENT3, ACCENT4],
                center_label=f"{int(df_collab['patents'].sum()):,}",
                center_sub="patents",
                figsize=(7, 5.5),
            ))

    with c3b:
        st.subheader("Inventor Productivity Tiers")
        df_inv_tiers = load_inventor_quartile_distribution()
        if not df_inv_tiers.empty:
            st.pyplot(exploded_pie_chart(
                df_inv_tiers["tier"].tolist(),
                df_inv_tiers["inventors"].tolist(),
                "Inventor Portfolio Tiers",
                highlight_n=1,
                figsize=(7, 5.5),
            ))

    with c3c:
        st.subheader("Radial — Collaboration Structure")
        if not df_collab.empty:
            st.pyplot(radial_bar_chart(
                df_collab["collab_tier"].tolist(),
                df_collab["patents"].tolist(),
                "Collaboration Tier Radial",
                colors=[ACCENT2, ACCENT, ACCENT3, ACCENT4],
                figsize=(6.5, 6.5),
            ))

    st.markdown("---")

    st.markdown("### Company Inventor Geography — Small Multiples")
    n_comp_sm = st.slider("Companies", 3, 6, 4, key="sm_comp_n")
    df_cbd2 = load_top_company_country_breakdown(n_comp_sm)
    if not df_cbd2.empty:
        groups_data2 = []
        for company in df_cbd2["company"].unique():
            sub = df_cbd2[df_cbd2["company"] == company].sort_values(
                "patents", ascending=False).head(7)
            groups_data2.append((company, sub["country"].tolist(), sub["patents"].tolist()))
        st.pyplot(stacked_donut_small_multiples(
            groups_data2,
            "Inventor Country Origin — Top Companies"
        ))
    else:
        st.warning("No company/country data.")

    st.markdown("---")

    st.markdown("### Decade × Country Nested Ring")
    df_dc = load_filing_decade_by_country(limit=5)
    if not df_dc.empty:
        pivot_dc = df_dc.pivot_table(
            index="country", columns="decade", values="patents", fill_value=0
        )
        country_totals = pivot_dc.sum(axis=1).sort_values(ascending=False)
        decade_order = ["Pre-1990", "1990s", "2000s", "2010s", "2020s"]
        decade_order = [d for d in decade_order if d in pivot_dc.columns]

        outer_labels = country_totals.index.tolist()
        outer_values = country_totals.values.tolist()

        inner_labels = []
        inner_values = []
        for ctry in outer_labels:
            for dec in decade_order:
                v = pivot_dc.loc[ctry, dec] if dec in pivot_dc.columns else 0
                if v > 0:
                    inner_labels.append(f"{ctry[:8]} {dec}")
                    inner_values.append(int(v))

        if inner_values:
            st.pyplot(nested_donut_chart(
                outer_labels, outer_values,
                inner_labels, inner_values,
                "Country (outer) × Decade (inner) — Nested Ring",
                figsize=(9, 6.5),
            ))

    st.markdown("---")
    st.markdown("### Composition KPIs")
    kc1, kc2, kc3, kc4 = st.columns(4)

    df_cs_k = load_country_share_extended(20)
    df_csh_k = load_company_patent_share(10)
    df_coll_k = load_inventor_collaboration_tiers()
    df_dec_k = load_decade_share()

    with kc1:
        if not df_cs_k.empty:
            top1 = df_cs_k.iloc[0]
            st.metric("Top Country Share",
                      top1["country"],
                      delta=f"{top1['share']:.1f}% of patents")
    with kc2:
        if not df_csh_k.empty:
            top3_share = df_csh_k[df_csh_k["company"] != "Others"].head(3)["share"].sum()
            st.metric("Top 3 Companies",
                      f"{top3_share:.1f}%",
                      delta="of all patents combined")
    with kc3:
        if not df_coll_k.empty:
            total_col = df_coll_k["patents"].sum()
            solo_row = df_coll_k[df_coll_k["collab_tier"] == "Solo"]
            solo_pct = (solo_row["patents"].values[0] / total_col * 100) if len(solo_row) > 0 else 0
            st.metric("Solo-filed Patents",
                      f"{solo_pct:.0f}%",
                      delta="filed by single inventor")
    with kc4:
        if not df_dec_k.empty:
            top_dec = df_dec_k.loc[df_dec_k["patents"].idxmax()]
            st.metric("Most Productive Decade",
                      top_dec["decade"],
                      delta=f"{int(top_dec['patents']):,} patents")


# ================================================================
# PAGE: COMPARATIVE MAP  (NEW)
# ================================================================
elif page == "Comparative Map":
    st.title("Comparative Map")
    st.markdown(
        "Interactive world maps and side-by-side country comparisons built directly "
        "from your patent database. Hover over any country for full details."
    )
    st.markdown('<span class="section-label label-map">Geographic</span>', unsafe_allow_html=True)

    # ── Load base data ────────────────────────────────────────────
    df_all = load_all_countries_patents()
    df_yearly = load_country_yearly_all()
    df_decade_raw = load_country_decade_pivot()
    df_top_cos = load_country_top_companies()

    if df_all.empty:
        st.error("No country data found in the database.")
        st.stop()

    # Enrich with ISO3 + share
    df_geo = _build_geo_df(df_all)
    total_patents = df_geo["patents"].sum()
    df_geo["share_pct"] = (df_geo["patents"] / total_patents * 100).round(2)

    # Decade pivot for grouped-bar chart
    if not df_decade_raw.empty:
        decade_pivot = df_decade_raw.pivot_table(
            index="country", columns="decade", values="patents", fill_value=0
        )
    else:
        decade_pivot = pd.DataFrame()

    # ── KPI row ───────────────────────────────────────────────────
    st.markdown("---")
    n_countries_mapped = len(df_geo)
    top_country = df_geo.iloc[0]
    runner_up = df_geo.iloc[1] if len(df_geo) > 1 else top_country

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Countries Mapped", f"{n_countries_mapped:,}",
              delta="with ISO-3 resolution")
    k2.metric("Top Country", top_country["country"],
              delta=f"{top_country['share_pct']:.1f}% of dataset")
    k3.metric("Runner-up", runner_up["country"],
              delta=f"{runner_up['share_pct']:.1f}% of dataset")
    k4.metric("Total Patents (mapped)", f"{int(df_geo['patents'].sum()):,}")

    # ── Section 1 — Choropleth world map ─────────────────────────
    st.markdown("---")
    st.markdown("### 🗺️ World Choropleth — Patent Output")
    st.caption(
        "Colour intensity = total patents attributed to inventors in that country. "
        "Hover for details. Use the Plotly toolbar to zoom and pan."
    )

    map_metric = st.radio(
        "Colour map by:",
        ["patents", "inventors", "companies"],
        horizontal=True,
        key="map_metric_radio",
    )

    colorscale_options = {
        "patents":   "Blues",
        "inventors": "Greens",
        "companies": "Oranges",
    }

    if map_metric in df_geo.columns:
        fig_choro = build_choropleth(
            df_geo,
            metric=map_metric,
            title=f"Patent Dataset — {map_metric.title()} by Country",
            colorscale=colorscale_options.get(map_metric, "Blues"),
        )
        st.plotly_chart(fig_choro, use_container_width=True)
    else:
        st.warning(f"Column '{map_metric}' not available.")

    # ── Section 2 — Bubble map ────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🫧 Bubble Map — Inventor Efficiency by Country")
    st.caption(
        "Bubble size = patent count. Colour = patents per inventor "
        "(warm = highly efficient, cool = many inventors per patent)."
    )

    if "inventors" in df_geo.columns:
        fig_bubble = build_bubble_map(
            df_geo,
            title="Patent Efficiency — Bubble Map (size = patents, colour = pat/inv)",
        )
        st.plotly_chart(fig_bubble, use_container_width=True)
    else:
        st.info("Inventor count data not available for bubble map.")

    # ── Section 3 — Side-by-side country comparison ───────────────
    st.markdown("---")
    st.markdown("### ⚖️ Side-by-Side Country Comparison")
    st.caption(
        "Select any countries to compare across multiple dimensions: "
        "total output, growth trajectory, decade breakdown, and rank over time."
    )

    all_country_names = sorted(df_geo["country"].tolist())
    default_sel = all_country_names[:min(5, len(all_country_names))]

    selected_countries = st.multiselect(
        "Select countries to compare",
        options=all_country_names,
        default=default_sel,
        key="map_country_sel",
    )

    if not selected_countries:
        st.info("Select at least one country above to see comparisons.")
    else:
        df_sel = df_geo[df_geo["country"].isin(selected_countries)].copy()

        # ── Row A: horizontal bar comparison ─────────────────────
        comp_col1, comp_col2, comp_col3 = st.columns(3)
        with comp_col1:
            st.subheader("Total Patents")
            st.pyplot(comparison_bar_mpl(df_sel, "patents",
                                         "Total Patents — Selected Countries"))
        with comp_col2:
            st.subheader("Unique Inventors")
            if "inventors" in df_sel.columns:
                st.pyplot(comparison_bar_mpl(df_sel, "inventors",
                                             "Unique Inventors — Selected Countries"))
            else:
                st.info("Inventor data unavailable.")
        with comp_col3:
            st.subheader("Global Share (%)")
            fig_share, ax_share = _fig(8, max(3.5, len(df_sel) * 0.52))
            df_s2 = df_sel.sort_values("share_pct", ascending=True)
            bar_colors_s = [PIE_PALETTE[i % len(PIE_PALETTE)] for i in range(len(df_s2))]
            ax_share.barh(df_s2["country"], df_s2["share_pct"],
                          color=bar_colors_s, edgecolor=BG_CARD,
                          linewidth=0.6, height=0.62, alpha=0.88)
            for i, (_, row) in enumerate(df_s2.iterrows()):
                ax_share.text(row["share_pct"] + 0.05, i,
                              f"{row['share_pct']:.2f}%", va="center",
                              fontsize=8, color=TEXT_2)
            ax_share.set_xlabel("Share of all patents (%)", fontsize=9)
            ax_share.set_title("Global Patent Share", fontsize=12,
                               fontweight="600", pad=10)
            plt.tight_layout(pad=1.4)
            st.pyplot(fig_share)

        # ── Row B: decade grouped bar ─────────────────────────────
        st.markdown("---")
        st.subheader("Patent Output by Decade — Grouped Comparison")
        st.caption("Side-by-side bars show how each country's share evolved across eras.")
        if not decade_pivot.empty:
            valid_sel = [c for c in selected_countries if c in decade_pivot.index]
            if valid_sel:
                st.pyplot(decade_grouped_bar(decade_pivot, valid_sel))
            else:
                st.warning("No decade data for selected countries.")
        else:
            st.warning("Decade data not available.")

        # ── Row C: YoY growth comparison ─────────────────────────
        st.markdown("---")
        comp_c1, comp_c2 = st.columns(2)

        with comp_c1:
            st.subheader("Year-over-Year Growth Rate")
            st.caption("Compare acceleration and deceleration patterns between countries.")
            if not df_yearly.empty:
                valid_yr = [c for c in selected_countries
                            if c in df_yearly["country"].unique()]
                if valid_yr:
                    st.pyplot(growth_comparison_chart(df_yearly, valid_yr))
                else:
                    st.warning("No annual data for selected countries.")
            else:
                st.warning("No yearly data available.")

        with comp_c2:
            st.subheader("Rank Trajectory")
            st.caption(
                "How each country's annual rank changed over the full dataset period. "
                "Rank 1 = most patents that year. Lines moving up = climbing in output."
            )
            if not df_yearly.empty:
                valid_yr2 = [c for c in selected_countries
                             if c in df_yearly["country"].unique()]
                if valid_yr2:
                    st.pyplot(rank_trajectory_chart(df_yearly, valid_yr2))
                else:
                    st.warning("No rank data for selected countries.")
            else:
                st.warning("No yearly data available.")

        # ── Row D: sparkline summary table ───────────────────────
        st.markdown("---")
        st.subheader("Country Summary — Snapshot Table")
        st.caption(
            "Key figures for each selected country, including top companies "
            "and the trend sparkline over time."
        )

        for country in selected_countries:
            row_data = df_sel[df_sel["country"] == country]
            if row_data.empty:
                continue
            row = row_data.iloc[0]

            # Top companies for this country
            top_cos_here = df_top_cos[df_top_cos["country"] == country]
            top_cos_str = ", ".join(top_cos_here["company"].tolist()[:3]) or "—"

            # Growth: first vs last available year
            yr_sub = df_yearly[df_yearly["country"] == country].sort_values("year")
            if len(yr_sub) >= 2:
                first_val = yr_sub["patents"].iloc[0]
                last_val  = yr_sub["patents"].iloc[-1]
                overall_g = ((last_val - first_val) / max(first_val, 1) * 100)
                growth_str = f"+{overall_g:.0f}%" if overall_g >= 0 else f"{overall_g:.0f}%"
            else:
                growth_str = "—"

            c_idx = selected_countries.index(country)
            c_color = PALETTE[c_idx % len(PALETTE)]

            with st.container():
                left, mid, right = st.columns([3, 6, 3])
                with left:
                    st.markdown(
                        f"**{country}**  \n"
                        f"<span style='color:{c_color};font-size:1.5rem;font-weight:700'>"
                        f"{int(row['patents']):,}</span> patents",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Global share: **{row['share_pct']:.2f}%**")
                    if "inventors" in row:
                        st.caption(f"Inventors: {int(row['inventors']):,}")
                    st.caption(f"Overall growth: {growth_str}")
                    st.caption(f"Top companies: {top_cos_str[:60]}")

                with mid:
                    if len(yr_sub) >= 3:
                        spark = sparkline_mpl(
                            yr_sub["year"].values,
                            yr_sub["patents"].values,
                            color=c_color,
                            w=4.5, h=1.0,
                        )
                        st.pyplot(spark, use_container_width=False)
                        plt.close(spark)
                        first_yr = int(yr_sub["year"].iloc[0])
                        last_yr  = int(yr_sub["year"].iloc[-1])
                        st.caption(f"Annual trend {first_yr}–{last_yr}")

                with right:
                    # Mini donut for decade share
                    if not df_decade_raw.empty and country in decade_pivot.index:
                        dec_vals = decade_pivot.loc[country]
                        dec_vals = dec_vals[dec_vals > 0]
                        if not dec_vals.empty:
                            mini_fig, mini_ax = plt.subplots(figsize=(2.2, 2.2))
                            mini_fig.patch.set_facecolor(BG_CARD)
                            mini_ax.set_facecolor(BG_CARD)
                            mini_ax.pie(
                                dec_vals.values,
                                colors=[PIE_PALETTE[i % len(PIE_PALETTE)]
                                        for i in range(len(dec_vals))],
                                startangle=90,
                                counterclock=False,
                                wedgeprops=dict(width=0.45, edgecolor=BG_CARD,
                                                linewidth=1.5),
                            )
                            mini_inner = plt.Circle((0, 0), 0.54, color=BG_CARD, zorder=3)
                            mini_ax.add_patch(mini_inner)
                            mini_ax.set_title("Decades", fontsize=7, color=TEXT_2, pad=4)
                            st.pyplot(mini_fig, use_container_width=False)
                            plt.close(mini_fig)

                st.markdown(
                    f"<hr style='border:1px solid #1e2433;margin:0.6rem 0;'>",
                    unsafe_allow_html=True,
                )

    # ── Section 4 — Top-20 sortable table ────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Full Country Rankings Table")
    st.caption("All countries with resolved ISO-3 codes, sorted by patents descending.")

    display_cols = ["country", "iso3", "patents", "share_pct"]
    if "inventors" in df_geo.columns:
        display_cols.append("inventors")
    if "companies" in df_geo.columns:
        display_cols.append("companies")

    df_table = df_geo[display_cols].sort_values("patents", ascending=False).reset_index(drop=True)
    df_table.index += 1
    df_table.columns = [c.replace("_", " ").title() for c in df_table.columns]
    st.dataframe(df_table, use_container_width=True)

    st.download_button(
        "Download Country Map Data",
        data=df_table.to_csv(index=False),
        file_name="patent_country_map_data.csv",
        mime="text/csv",
    )