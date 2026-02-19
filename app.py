import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 3D molecules + PDF
import py3Dmol
from stpy3Dmol import stpy3Dmol
from fpdf import FPDF

st.set_page_config(page_title="AstroBioChem Explorer", layout="wide")
st.title("Hunter's AstroBioChem Explorer")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🧪 Habitability Score")
st.sidebar.write("""
Score (0–100) based on:
- Temperature: 250–350 K → good
- Planet radius: 0.5–2.0 Earth radii → rocky
- Stellar temperature: G/K stars preferred
- Atmosphere: placeholder for future data
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

# ---------------- HABITABILITY LOGIC ----------------
def habitability_components(row):
    temp = radius = star = atmosphere = 0

    if pd.notnull(row["pl_eqt"]):
        temp = 30 if 250 <= row["pl_eqt"] <= 350 else max(0, 30 - abs(row["pl_eqt"] - 300) / 5)

    if pd.notnull(row["pl_rade"]):
        radius = 30 if 0.5 <= row["pl_rade"] <= 2.0 else max(0, 30 - abs(row["pl_rade"] - 1.25) * 15)

    if pd.notnull(row["st_teff"]):
        star = 20 if 3700 <= row["st_teff"] <= 6000 else 10

    atmosphere = 0  # future expansion

    return temp, radius, star, atmosphere

def habitability_score(row):
    return min(sum(habitability_components(row)), 100)

df["habitability"] = df.apply(habitability_score, axis=1)

# ---------------- PLANET SELECTION ----------------
st.subheader("🪐 Select a Planet")
planet_name = st.selectbox("Choose a planet:", df["pl_name"])
planet = df[df["pl_name"] == planet_name].iloc[0]

# ---------------- PLANET PROFILE CARD ----------------
st.subheader("📌 Planet Profile")
c1, c2, c3 = st.columns(3)
c1.metric("Temperature (K)", round(planet["pl_eqt"], 1))
c2.metric("Radius (Earth)", round(planet["pl_rade"], 2))
c3.metric("Habitability Score", int(planet["habitability"]))

# ---------------- SCORE BREAKDOWN ----------------
components = habitability_components(planet)
breakdown_df = pd.DataFrame({
    "Factor": ["Temperature", "Radius", "Star Type", "Atmosphere"],
    "Score": components
})

st.subheader("🧬 Habitability Score Breakdown")
st.bar_chart(breakdown_df.set_index("Factor"))

# ---------------- MOLECULE SELECTION ----------------
st.subheader("🧠 Plausible Biomolecule")

pdb_map = {
    "rubisco": "molecules/1RUB.pdb",
    "antifreeze": "molecules/1AFP.pdb",
    "sod": "molecules/2SOD.pdb",
    "lysozyme": "molecules/1LYZ.pdb"
}

# Rule-based molecule choice
if planet["pl_eqt"] < 250:
    pdb_file = pdb_map["antifreeze"]
elif planet["habitability"] > 80:
    pdb_file = pdb_map["rubisco"]
elif planet["st_teff"] > 6000:
    pdb_file = pdb_map["sod"]
else:
    pdb_file = pdb_map["lysozyme"]

# ---------------- 3D MOLECULE VIEWER ----------------
if os.path.exists(pdb_file):
    view = py3Dmol.view(width=800, height=500)
    view.addModel(open(pdb_file).read(), "pdb")
    view.setStyle({"cartoon": {"color": "spectrum"}})
    view.zoomTo()
    stpy3Dmol(view, key=planet_name)
else:
    st.warning(f"PDB file not found: {pdb_file}")

# ---------------- PDF EXPORT ----------------
def generate_pdf(planet):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, f"Planet: {planet['pl_name']}", ln=True)
    pdf.cell(0, 10, f"Host Star: {planet['hostname']}", ln=True)
    pdf.cell(0, 10, f"Temperature: {planet['pl_eqt']} K", ln=True)
    pdf.cell(0, 10, f"Radius: {planet['pl_rade']} Earth radii", ln=True)
    pdf.cell(0, 10, f"Habitability Score: {planet['habitability']}", ln=True)

    path = f"{planet['pl_name']}_report.pdf"
    pdf.output(path)
    return path

if st.button("📄 Export Planet PDF Report"):
    pdf_path = generate_pdf(planet)
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="Download PDF",
            data=f,
            file_name=pdf_path,
            mime="application/pdf"
        )

# ---------------- DATA TABLE ----------------
st.subheader("🔍 Exoplanet Dataset")
search = st.text_input("Search by planet or star name:")

filtered_df = df[
    df["pl_name"].str.contains(search, case=False, na=False) |
    df["hostname"].str.contains(search, case=False, na=False)
] if search else df

filtered_df = filtered_df.sort_values(by="habitability", ascending=False)
st.dataframe(filtered_df, use_container_width=True)

# ---------------- SCATTER PLOTS ----------------
st.subheader("📊 Planet Radius vs Temperature (Discovery Facility)")
fig = px.scatter(
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
st.plotly_chart(fig, use_container_width=True)

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
