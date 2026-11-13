import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="ICU Capacity — DMI Analytics",
    page_icon="🏥",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Design tokens
# Identity: deep teal + mid teal on warm sand, signal coral as the contrast accent.
# ---------------------------------------------------------------------------
COLOR_BG = "#F5EFE4"            # warm sand
COLOR_TEXT = "#0E2A2B"          # ink teal
COLOR_MUTED = "#5E706E"
COLOR_PRIMARY = "#0F3D3E"       # deep teal
COLOR_PRIMARY_MID = "#2A7F7A"   # mid teal
COLOR_ACCENT = "#FF5A3C"        # signal coral
COLOR_BORDER = "#DCD3C2"
COLOR_SIDEBAR_BG = "#0B2F30"
COLOR_SIDEBAR_TEXT = "#EDE6D8"

THRESHOLD = 0.90

# Anton = heavy condensed display, Bebas Neue = labels, Yellowtail = script accent,
# DM Sans = interface text.
FONT_IMPORT = (
    "https://fonts.googleapis.com/css2?"
    "family=Anton&family=Bebas+Neue&family=Yellowtail"
    "&family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap"
)

st.markdown(f"""
<style>
@import url('{FONT_IMPORT}');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
}}

/* ---------- Page: full warm sand, with soft shapes behind the content ---------- */
.stApp {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    isolation: isolate;
}}
.stApp::before {{
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background:
        radial-gradient(circle 340px at 100% 100%, {COLOR_PRIMARY_MID}26 0, {COLOR_PRIMARY_MID}26 99%, transparent 100%),
        radial-gradient(circle 150px at 38% 112%, {COLOR_PRIMARY}14 0, {COLOR_PRIMARY}14 99%, transparent 100%);
}}

/* Top bar: same colour as the page, no coloured strip */
header[data-testid="stHeader"] {{
    background: transparent;
}}
[data-testid="stDecoration"] {{
    display: none;
}}
header[data-testid="stHeader"] *,
[data-testid="stToolbar"] * {{
    color: {COLOR_PRIMARY} !important;
}}

.block-container {{
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1240px;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background-color: {COLOR_SIDEBAR_BG};
    border-right: 4px solid {COLOR_ACCENT};
}}
section[data-testid="stSidebar"] * {{
    color: {COLOR_SIDEBAR_TEXT} !important;
}}
section[data-testid="stSidebar"] [data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-baseweb="input"] * {{
    color: {COLOR_TEXT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stDateInput"] * {{
    color: {COLOR_TEXT} !important;
    -webkit-text-fill-color: {COLOR_TEXT} !important;
}}
section[data-testid="stSidebar"] [data-testid="stDateInput"] label,
section[data-testid="stSidebar"] [data-testid="stDateInput"] label * {{
    color: {COLOR_SIDEBAR_TEXT} !important;
    -webkit-text-fill-color: {COLOR_SIDEBAR_TEXT} !important;
}}
section[data-testid="stSidebar"] input {{
    color: {COLOR_TEXT} !important;
    -webkit-text-fill-color: {COLOR_TEXT} !important;
    opacity: 1 !important;
}}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background-color: {COLOR_ACCENT} !important;
}}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] * {{
    color: #fff !important;
}}
.sidebar-title {{
    font-family: 'Anton', sans-serif;
    font-size: 2.3rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    line-height: 0.95;
    margin: 0.25rem 0 0.4rem 0;
}}
.sidebar-script {{
    font-family: 'Yellowtail', cursive;
    font-size: 1.5rem;
    color: {COLOR_ACCENT} !important;
    margin: -0.2rem 0 0.6rem 0;
    transform: rotate(-3deg);
    display: inline-block;
}}
.sidebar-note {{
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 1.2rem;
}}

/* ---------- Hero: type + shapes straight on the sand ---------- */
.hero {{
    position: relative;
    padding: 0.5rem 0 1.6rem 0;
}}
.hero-shape {{
    position: absolute;
    border-radius: 50%;
    z-index: 0;
    pointer-events: none;
}}
.hero-shape.s1 {{ width: 360px; height: 360px; right: -30px; top: -20px; background: {COLOR_PRIMARY_MID}; opacity: 0.92; }}
.hero-shape.s2 {{ width: 150px; height: 150px; right: 235px; top: 270px; background: {COLOR_ACCENT}; }}
.hero-shape.s3 {{ width: 130px; height: 130px; right: 20px; top: 290px; border: 16px solid {COLOR_PRIMARY}; background: transparent; }}
.hero-shape.s4 {{ width: 46px; height: 46px; right: 372px; top: 34px; background: {COLOR_PRIMARY}; }}

.hero-meta {{
    position: relative; z-index: 1;
    display: flex; flex-wrap: wrap; gap: 0.4rem 2rem;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {COLOR_PRIMARY};
    margin-bottom: 1rem;
}}
.hero-meta span::before {{
    content: "";
    display: block;
    width: 22px; height: 2px;
    background: {COLOR_ACCENT};
    margin-bottom: 0.35rem;
}}
.hero-title {{
    position: relative; z-index: 1;
    font-family: 'Anton', sans-serif;
    font-weight: 400;
    font-size: clamp(3.6rem, 10.5vw, 9rem);
    line-height: 0.88;
    letter-spacing: 0.005em;
    text-transform: uppercase;
    color: {COLOR_PRIMARY};
    margin: 0;
}}
.hero-title .l1 {{ display: block; position: relative; width: fit-content; }}
.hero-title .l2 {{ display: block; margin-left: clamp(1rem, 5vw, 4.5rem); }}
.hero-script {{
    position: absolute; z-index: 2;
    right: -0.5em;
    bottom: -0.32em;
    font-family: 'Yellowtail', cursive;
    font-size: 0.46em;
    line-height: 1;
    text-transform: none;
    color: {COLOR_ACCENT};
    transform: rotate(-7deg);
    white-space: nowrap;
    pointer-events: none;
}}
.hero-desc {{
    position: relative; z-index: 1;
    max-width: 560px;
    margin: 1.6rem 0 0 0;
    font-family: 'Inter', sans-serif;
    font-size: 0.98rem;
    line-height: 1.6;
    color: {COLOR_TEXT};
}}
.hero-desc::before {{
    content: "///";
    display: block;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 0.1em;
    color: {COLOR_ACCENT};
    margin-bottom: 0.2rem;
}}
.hero-vert {{
    position: absolute; z-index: 1;
    right: 138px; top: 70px;
    writing-mode: vertical-rl;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.15rem;
    letter-spacing: 0.3em;
    color: {COLOR_BG};
}}
@media (max-width: 900px) {{
    .hero-shape.s1 {{ width: 220px; height: 220px; right: -60px; top: -30px; opacity: 0.35; }}
    .hero-shape.s2, .hero-shape.s3, .hero-shape.s4, .hero-vert {{ display: none; }}
    .hero-script {{ right: -0.2em; }}
}}

/* ---------- Section headings ---------- */
.section-head {{
    display: flex;
    align-items: flex-end;
    gap: 1.1rem;
    margin: 3.2rem 0 0 0;
}}
.sh-num {{
    font-family: 'Anton', sans-serif;
    font-size: clamp(3.4rem, 7vw, 5rem);
    line-height: 0.82;
    color: transparent;
    -webkit-text-stroke: 2px {COLOR_ACCENT};
}}
.sh-title {{
    position: relative;
    font-family: 'Anton', sans-serif;
    font-size: clamp(2.3rem, 5.4vw, 3.8rem);
    line-height: 0.9;
    text-transform: uppercase;
    color: {COLOR_PRIMARY};
}}
.sh-script {{
    font-family: 'Yellowtail', cursive;
    font-size: clamp(1.9rem, 4.2vw, 3rem);
    line-height: 1;
    color: {COLOR_ACCENT};
    margin-left: -0.9rem;
    transform: translateY(0.55rem) rotate(-6deg);
    white-space: nowrap;
    position: relative; z-index: 2;
}}
.sh-rule {{
    height: 3px;
    background: {COLOR_PRIMARY};
    margin: 0.9rem 0 0.5rem 0;
}}
.sh-sub {{
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {COLOR_MUTED};
    margin-bottom: 1.1rem;
}}

/* ---------- KPIs (no filled boxes — rules and big numerals) ---------- */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.8rem;
    margin: 0.6rem 0 0.5rem 0;
}}
@media (max-width: 900px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 520px) {{
    .kpi-grid {{ grid-template-columns: 1fr; }}
}}
.kpi {{
    border-top: 6px solid {COLOR_PRIMARY};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 0.7rem 0 1rem 0;
}}
.kpi.alert {{
    border-top-color: {COLOR_ACCENT};
}}
.kpi-label {{
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {COLOR_MUTED};
    margin-bottom: 0.2rem;
}}
.kpi-value {{
    font-family: 'Anton', sans-serif;
    font-size: clamp(3.2rem, 5.4vw, 4.6rem);
    line-height: 1;
    color: {COLOR_PRIMARY};
}}
.kpi.alert .kpi-value {{
    color: {COLOR_ACCENT};
}}
.kpi-bar {{
    height: 6px;
    background: {COLOR_BORDER};
    margin-top: 0.7rem;
    border-radius: 3px;
    overflow: hidden;
}}
.kpi-bar > span {{
    display: block;
    height: 100%;
    background: {COLOR_PRIMARY_MID};
}}
.kpi-bar.hot > span {{
    background: {COLOR_ACCENT};
}}

/* ---------- Table, inputs ---------- */
[data-testid="stDataFrame"] {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 3px;
    overflow: hidden;
}}
.stSelectbox label, .stMultiSelect label {{
    font-weight: 700;
    letter-spacing: 0.04em;
    color: {COLOR_PRIMARY};
}}

.empty-state {{
    border: 1px dashed {COLOR_PRIMARY_MID};
    border-left: 5px solid {COLOR_ACCENT};
    padding: 1rem 1.2rem;
    color: {COLOR_MUTED};
    border-radius: 3px;
}}

.footer-note {{
    margin-top: 3rem;
    padding-top: 0.8rem;
    border-top: 1px solid {COLOR_BORDER};
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {COLOR_MUTED};
}}

hr {{
    border-color: {COLOR_BORDER};
}}
</style>
""", unsafe_allow_html=True)


def section_head(num: str, title: str, script: str, sub: str) -> None:
    st.markdown(
        f"<div class='section-head'><span class='sh-num'>{num}</span>"
        f"<span class='sh-title'>{title}</span>"
        f"<span class='sh-script'>{script}</span></div>"
        f"<div class='sh-rule'></div><div class='sh-sub'>{sub}</div>",
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.markdown(f"<div class='empty-state'>{message}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <span class="hero-shape s1"></span>
        <span class="hero-shape s2"></span>
        <span class="hero-shape s3"></span>
        <span class="hero-shape s4"></span>
        <div class="hero-meta">
            <span>DMI Analytics</span>
            <span>NRW &times; Sachsen</span>
            <span>Simulated data</span>
        </div>
        <div class="hero-title" role="heading" aria-level="1"><span class="l1">ICU Bed<span class="hero-script">at a glance</span></span><span class="l2">Capacity</span></div>
        <p class="hero-desc">
            A synthetic-data pipeline for ICU capacity monitoring. It ingests 90 days of
            occupancy records for 15 fictional hospitals in NRW and Saxony, checks their
            quality, and pseudonymizes facility IDs with SHA-256. The dashboard then shows
            which hospitals ran above 90% occupancy, and when, without exposing facility
            identities.
        </p>
        <div class="hero-vert">90% THRESHOLD</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    file_path = os.path.join("data", "processed", "icu_beds_anonymized.csv")
    if not os.path.exists(file_path):
        st.error(
            f"Processed data not found at {file_path}. Run "
            "generate_synthetic_data.py, then ingest_data.py, then anonymize.py first."
        )
        return None
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


df = load_data()

if df is not None:
    st.sidebar.markdown(
        "<div class='sidebar-title'>Filter<br>records</div>"
        "<div class='sidebar-script'>your view</div>"
        "<div class='sidebar-note'>State &middot; Period</div>",
        unsafe_allow_html=True,
    )
    regions = sorted(df["bundesland"].unique())
    selected_regions = st.sidebar.multiselect("State (Bundesland)", regions, default=regions)

    min_date, max_date = df["date"].min(), df["date"].max()
    date_range = st.sidebar.date_input(
        "Date range", (min_date, max_date), min_value=min_date, max_value=max_date
    )

    mask = df["bundesland"].isin(selected_regions)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        mask &= df["date"].between(start, end)
    filtered_df = df[mask]

    avg_occ = filtered_df["occupancy_rate"].mean() if len(filtered_df) else 0
    over_count = int(filtered_df["over_threshold"].sum()) if len(filtered_df) else 0
    occ_pct = max(0.0, min(avg_occ, 1.0)) * 100
    occ_hot = "hot" if avg_occ >= THRESHOLD else ""

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-label">Facility-days analyzed</div>
            <div class="kpi-value">{len(filtered_df):,}</div>
        </div>
        <div class="kpi">
            <div class="kpi-label">Anonymized facilities</div>
            <div class="kpi-value">{filtered_df['facility_hash'].nunique()}</div>
        </div>
        <div class="kpi">
            <div class="kpi-label">Average occupancy</div>
            <div class="kpi-value">{avg_occ:.0%}</div>
            <div class="kpi-bar {occ_hot}"><span style="width:{occ_pct:.1f}%"></span></div>
        </div>
        <div class="kpi alert">
            <div class="kpi-label">Facility-days over 90%</div>
            <div class="kpi-value">{over_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    section_head("01", "Over capacity", "facilities", "Facilities over the 90% threshold &middot; highest occupancy first")
    over_df = filtered_df[filtered_df["over_threshold"]].sort_values("occupancy_rate", ascending=False)
    if len(over_df) > 0:
        display_df = over_df[["date", "bundesland", "facility_hash", "occupancy_rate", "available_beds"]].copy()
        display_df["occupancy_rate"] = display_df["occupancy_rate"] * 100
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "bundesland": st.column_config.TextColumn("State"),
                "facility_hash": st.column_config.TextColumn("Facility (anonymized)"),
                "occupancy_rate": st.column_config.ProgressColumn(
                    "Occupancy", format="%.1f%%", min_value=0, max_value=120
                ),
                "available_beds": st.column_config.NumberColumn("Available beds"),
            },
        )
    else:
        empty_state(
            "No facilities crossed the 90% occupancy threshold in this selection."
        )

    section_head("02", "Occupancy", "trend", "Daily occupancy rate for one anonymized facility")
    facility_options = sorted(filtered_df["facility_hash"].unique())
    if facility_options:
        selected_facility = st.selectbox("Facility (anonymized ID)", facility_options)
        trend_df = filtered_df[filtered_df["facility_hash"] == selected_facility].sort_values("date")

        fig, ax = plt.subplots(figsize=(10, 3.8))
        fig.patch.set_facecolor((0, 0, 0, 0))   # transparent: sits directly on the sand
        ax.set_facecolor((0, 0, 0, 0))
        ax.fill_between(
            trend_df["date"], trend_df["occupancy_rate"],
            color=COLOR_PRIMARY_MID, alpha=0.14,
        )
        ax.plot(trend_df["date"], trend_df["occupancy_rate"], color=COLOR_PRIMARY, linewidth=2.6)
        ax.axhline(THRESHOLD, color=COLOR_ACCENT, linestyle="--", linewidth=1.5, label="90% threshold")
        over_pts = trend_df[trend_df["occupancy_rate"] > THRESHOLD]
        if len(over_pts):
            ax.scatter(over_pts["date"], over_pts["occupancy_rate"], color=COLOR_ACCENT, s=28, zorder=3)
        ax.set_ylim(0, 1.2)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
        ax.set_ylabel("Occupancy rate", color=COLOR_TEXT)
        ax.tick_params(colors=COLOR_MUTED)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(COLOR_BORDER)
        ax.grid(axis="y", color=COLOR_BORDER, linewidth=0.7, alpha=0.8)
        ax.legend(frameon=False, labelcolor=COLOR_MUTED, loc="upper left")
        fig.autofmt_xdate()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        empty_state("No data for the current filter selection.")

st.markdown(
    "<div class='footer-note'>DMI Analytics &nbsp;/&nbsp; Simulated data &nbsp;/&nbsp; "
    "DSGVO-style anonymization</div>",
    unsafe_allow_html=True,
)