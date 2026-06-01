import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# ================= PAGE SETUP =================
st.set_page_config(
    page_title="AstroBioChem Explorer",
    layout="wide"
)

st.title("🔭 AstroBioChem Explorer")
st.write(
    "An interactive research tool exploring **exoplanet habitability** using "
    "real NASA data and biochemistry-inspired scoring models."
)

# ================= SIDEBAR =================
st.sidebar.header("🧪 Habitability Model")
st.sidebar.markdown("""
**Score (0–100) based on:**
- 🌡️ Equilibrium temperature  
- 🪐 Planet radius (rocky vs gas)  
- ⭐ Host star temperature  
- 🧬 Atmospheric indicators (future expansion)

This model is **transparent and heuristic**, designed for comparative analysis.
""")

# ================= DATA LOADING =================
@st.cache_data
def load_exoplanet_data():
    url = (
        "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
        "query=select+pl_name,hostname,disc_year,pl_rade,"
        "pl_masse,pl_eqt,st_teff,st_mass,disc_facility+"
        "from+pscomppars+where+pl_eqt+is+not+null"
        "&format=csv"
    )
    return pd.read_csv(url)

df = load_exoplanet_data()

# ================= HABITABILITY MODEL =================
def habitability_components(row):
    temp_score = radius_score = star_score = atmosphere_score = 0

    # Temperature (ideal ~300 K)
    if pd.notnull(row["pl_eqt"]):
        if 250 <= row["pl_eqt"] <= 350:
            temp_score = 30
        else:
            temp_score = max(0, 30 - abs(row["pl_eqt"] - 300) / 5)

    # Radius (rocky planets)
    if pd.notnull(row["pl_rade"]):
        if 0.5 <= row["pl_rade"] <= 2.0:
            radius_score = 30
        else:
            radius_score = max(0, 30 - abs(row["pl_rade"] - 1.25) * 15)

    # Star temperature
    if pd.notnull(row["st_teff"]):
        if 3700 <= row["st_teff"] <= 6000:
            star_score = 20
        else:
            star_score = 10

    return temp_score, radius_score, star_score, atmosphere_score

def habitability_score(row):
    return min(sum(habitability_components(row)), 100)

df["habitability"] = df.apply(habitability_score, axis=1)

# ================= PLANET SELECTION =================
st.divider()
st.subheader("🪐 Explore a Planet")

planet_name = st.selectbox(
    "Choose a confirmed exoplanet:",
    df["pl_name"].sort_values()
)
planet = df[df["pl_name"] == planet_name].iloc[0]

# ================= PLANET PROFILE =================
st.subheader("📌 Planet Profile")

c1, c2, c3 = st.columns(3)
c1.metric("Equilibrium Temp (K)", round(planet["pl_eqt"], 1))
c2.metric("Radius (Earth)", round(planet["pl_rade"], 2))
c3.metric("Habitability Score", int(planet["habitability"]))

# ================= SCORE BREAKDOWN =================
st.subheader("🧬 Habitability Score Breakdown")

scores = habitability_components(planet)
breakdown_df = pd.DataFrame({
    "Factor": ["Temperature", "Planet Size", "Star Type", "Atmosphere"],
    "Score": scores
})

st.bar_chart(breakdown_df.set_index("Factor"))

# ================= BIOMOLECULE ANALYSIS =================
st.subheader("🧬 Plausible Biomolecule")

molecule_data = {
    "Antifreeze Protein": {
        "reason": "Selected because this planet has a very low equilibrium temperature.",
        "function": "Prevents ice crystal formation inside cells.",
        "astrobiology": "Could help hypothetical life survive on cold worlds where liquid water is scarce."
    },
    "Rubisco": {
        "reason": "Selected because this planet scored highly on the habitability index.",
        "function": "Enzyme responsible for carbon fixation during photosynthesis.",
        "astrobiology": "Could support Earth-like biological energy cycles on potentially habitable planets."
    },
    "Superoxide Dismutase (SOD)": {
        "reason": "Selected because the host star is relatively hot and may produce higher radiation levels.",
        "function": "Protects cells from oxidative damage caused by reactive oxygen species.",
        "astrobiology": "Could be essential for life exposed to elevated radiation environments."
    },
    "Lysozyme": {
        "reason": "Selected as a general-purpose biomolecule for less favorable environments.",
        "function": "Breaks down bacterial cell walls and contributes to cellular defense.",
        "astrobiology": "Represents a simple, robust protein that could remain useful in a wide range of conditions."
    }
}

# Select molecule based on planet properties
if planet["pl_eqt"] < 250:
    molecule = "Antifreeze Protein"
elif planet["habitability"] > 80:
    molecule = "Rubisco"
elif planet["st_teff"] > 6000:
    molecule = "Superoxide Dismutase (SOD)"
else:
    molecule = "Lysozyme"

info = molecule_data[molecule]

st.markdown(f"### {molecule}")

st.write(f"**Why it was selected:** {info['reason']}")

st.write(f"**Biological Function:** {info['function']}")

st.write(f"**Astrobiology Relevance:** {info['astrobiology']}")

st.info(
    "This biomolecule is a conceptual example used to explore how different biological "
    "adaptations might help life survive under various planetary conditions."
)
# ================= REPORT EXPORT =================
st.subheader("📄 Export Planet Report")

def generate_report(planet):
    report = f"""
AstroBioChem Explorer — Planet Report

Planet Name: {planet['pl_name']}
Host Star: {planet['hostname']}
Discovery Year: {planet['disc_year']}

Equilibrium Temperature: {planet['pl_eqt']} K
Planet Radius: {planet['pl_rade']} Earth radii
Estimated Habitability Score: {int(planet['habitability'])}/100

Scoring based on planetary temperature, size,
and stellar properties using NASA Exoplanet Archive data.
"""
    buffer = BytesIO()
    buffer.write(report.encode("utf-8"))
    buffer.seek(0)
    return buffer

st.download_button(
    "⬇️ Download Report",
    generate_report(planet),
    file_name=f"{planet['pl_name']}_report.txt",
    mime="text/plain"
)

# ================= DATASET TABLE =================
st.divider()
st.subheader("🔍 Full Exoplanet Dataset")

search = st.text_input("Search by planet or star name:")

filtered_df = df[
    df["pl_name"].str.contains(search, case=False, na=False) |
    df["hostname"].str.contains(search, case=False, na=False)
] if search else df

st.dataframe(
    filtered_df.sort_values("habitability", ascending=False),
    use_container_width=True
)

# ================= VISUALIZATIONS =================
st.subheader("📊 Planet Radius vs Temperature (Discovery Facility)")

fig1 = px.scatter(
    df,
    x="pl_eqt",
    y="pl_rade",
    color="disc_facility",
    hover_name="pl_name",
    labels={
        "pl_eqt": "Equilibrium Temperature (K)",
        "pl_rade": "Planet Radius (Earth radii)"
    }
)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("📊 Planet Radius vs Temperature (Habitability Score)")

fig2 = px.scatter(
    df,
    x="pl_eqt",
    y="pl_rade",
    color="habitability",
    hover_name="pl_name",
    color_continuous_scale="Viridis",
    labels={
        "pl_eqt": "Equilibrium Temperature (K)",
        "pl_rade": "Planet Radius (Earth radii)",
        "habitability": "Habitability Score"
    }
)
st.plotly_chart(fig2, use_container_width=True)
