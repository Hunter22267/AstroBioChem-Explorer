import streamlit as st
import pandas as pd
import plotly.express as px
import py3Dmol
import os
from io import BytesIO
import streamlit.components.v1 as components

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="AstroBioChem Explorer", layout="wide")
st.title("Hunter's AstroBioChem Explorer")
st.write("Exploring real NASA exoplanet data with biochemistry-based habitability models 🌍🧬")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🧪 Habitability Score Model")
st.sidebar.write("""
**Score (0–100)** based on:
- 🌡️ Temperature (250–350 K ideal)
- 🪐 Planet radius (0.5–2.0 Earth radii)
- ⭐ Stellar temperature (G/K preferred)
- 🧬 Atmosphere (future expansion)
""")

# ---------------- DATA LOADING ----------------
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

# ---------------- HABITABILITY MODEL ----------------
def habitability_components(row):
    temp = radius = star = atmosphere = 0

    if pd.notnull(row["pl_eqt"]):
        temp = 30 if 250 <= row["pl_eqt"] <= 350 else max(0, 30 - abs(row["pl_eqt"] - 300) / 5)

    if pd.notnull(row["pl_rade"]):
        radius = 30 if 0.5 <= row["pl_rade"] <= 2.0 else max(0, 30 - abs(row["pl_rade"] - 1.25) * 15)

    if pd.notnull(row["st_teff"]):
        star = 20 if 3700 <= row["st_teff"] <= 6000 else 10

    return temp, radius, star, atmosphere

def habitability_score(row):
    return min(sum(habitability_components(row)), 100)

df["habitability"] = df.apply(habitability_score, axis=1)

# ---------------- PLANET SELECTION ----------------
st.divider()
st.subheader("🪐 Select a Planet")
planet_name = st.selectbox("Choose a planet:", df["pl_name"])
planet = df[df["pl_name"] == planet_name].iloc[0]

# ---------------- PLANET PROFILE ----------------
st.subheader("📌 Planet Profile")
c1, c2, c3 = st.columns(3)
c1.metric("Temperature (K)", round(planet["pl_eqt"], 1))
c2.metric("Radius (Earth)", round(planet["pl_rade"], 2))
c3.metric("Habitability Score", int(planet["habitability"]))

# ---------------- SCORE BREAKDOWN ----------------
components_scores = habitability_components(planet)
breakdown_df = pd.DataFrame({
    "Factor": ["Temperature", "Radius", "Star Type", "Atmosphere"],
    "Score": components_scores
})

st.subheader("🧬 Habitability Score Breakdown")
st.bar_chart(breakdown_df.set_index("Factor"))

# ---------------- MOLECULE SELECTION ----------------
st.subheader("🧠 Plausible Biomolecule (3D)")

pdb_map = {
    "rubisco": "molecules/1RUB.pdb",
    "antifreeze": "molecules/1AFP.pdb",
    "sod": "molecules/2SOD.pdb",
    "lysozyme": "molecules/1LYZ.pdb"
}

if planet["pl_eqt"] < 250:
    pdb_file = pdb_map["antifreeze"]
elif planet["habitability"] > 80:
    pdb_file = pdb_map["rubisco"]
elif planet["st_teff"] > 6000:
    pdb_file = pdb_map["sod"]
else:
    pdb_file = pdb_map["lysozyme"]

if os.path.exists(pdb_file):
    view = py3Dmol.view(width=800, height=500)
    view.addModel(open(pdb_file).read(), "pdb")
    view.setStyle({"cartoon": {"color": "spectrum"}})
    view.zoomTo()

    components.html(view._repr_html_(), height=550)
else:
    st.warning(f"Missing PDB file: {pdb_file}")

# ---------------- REPORT EXPORT (CLOUD SAFE) ----------------
st.subheader("📄 Export Planet Report")

def generate_report(planet):
    report = f"""
AstroBioChem Explorer – Planet Report

Planet: {planet['pl_name']}
Host Star: {planet['hostname']}
Discovery Year: {planet['disc_year']}

Equilibrium Temperature: {planet['pl_eqt']} K
Planet Radius: {planet['pl_rade']} Earth radii
Habitability Score: {int(planet['habitability'])}/100

Generated using NASA Exoplanet Archive data.
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

# ---------------- SEARCHABLE TABLE ----------------
st.divider()
st.subheader("🔍 Exoplanet Dataset")

search = st.text_input("Search by planet or star name:")
filtered_df = df[
    df["pl_name"].str.contains(search, case=False, na=False) |
    df["hostname"].str.contains(search, case=False, na=False)
] if search else df

st.dataframe(
    filtered_df.sort_values("habitability", ascending=False),
    use_container_width=True
)

# ---------------- SCATTER PLOTS ----------------
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

st.subheader("📊 Planet Radius vs Temperature (Habitability)")
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
