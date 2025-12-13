import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="AstroBioChem Explorer", layout="wide")
st.title("Hunter's AstroBioChem Explorer")

st.sidebar.title("🧪 Habitability Score")
st.sidebar.write("""
Score (0–100) based on:
- Temperature: 250–350 K → good
- Planet radius: 0.5–2.0 Earth radii → rocky & habitable
- Stellar type: G, K, quiet M → better
- Atmosphere: H₂O / CO₂ presence → bonus points
""")

st.write("Exploring real NASA exoplanet data 🌍🪐")
st.divider()

# Load NASA exoplanet data
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

# Habitability score
def habitability_score(row):
    score = 0
    if pd.notnull(row["pl_eqt"]):
        if 250 <= row["pl_eqt"] <= 350:
            score += 30
        else:
            score += max(0, 30 - abs(row["pl_eqt"]-300)/5)
    if pd.notnull(row["pl_rade"]):
        if 0.5 <= row["pl_rade"] <= 2.0:
            score += 30
        else:
            score += max(0, 30 - abs(row["pl_rade"]-1.25)*15)
    if pd.notnull(row["st_teff"]):
        if 3700 <= row["st_teff"] <= 5200:
            score += 20
        elif 5200 < row["st_teff"] <= 6000:
            score += 20
    score += 0
    return min(score, 100)

df["habitability"] = df.apply(habitability_score, axis=1)

# Planet selection
st.subheader("Select a Planet to See its Biomolecule")
planet_name = st.selectbox("Choose a planet:", df["pl_name"])
planet = df[df["pl_name"]==planet_name].iloc[0]

# Map molecules to planet conditions
img_file = "molecules/3ARC.png"  # default
if planet["pl_eqt"] < 250:
    img_file = "molecules/1AFP.png"
elif planet["habitability"] > 80:
    img_file = "molecules/1RUB.png"
elif planet["st_teff"] > 6000:
    img_file = "molecules/2SOD.png"
elif 3000 <= planet["st_teff"] <= 3700:
    img_file = "molecules/1HRC.png"
elif 0 <= planet["habitability"] <= 40:
    img_file = "molecules/1LYZ.png"
elif 60 < planet["habitability"] <= 80:
    img_file = "molecules/1HHO.png"

# Show molecule
if os.path.exists(img_file):
    st.image(img_file, caption=os.path.basename(img_file).replace(".png",""), use_column_width=True)
else:
    st.warning(f"Molecule image not found: {img_file}")

# Searchable table
st.subheader("🔍 Exoplanet Dataset with Habitability Score")
search = st.text_input("Search by planet or star name:")

if search:
    filtered_df = df[
        df["pl_name"].str.contains(search, case=False, na=False) |
        df["hostname"].str.contains(search, case=False, na=False)
    ]
else:
    filtered_df = df

filtered_df = filtered_df.sort_values(by="habitability", ascending=False)
st.dataframe(filtered_df, use_container_width=True)

st.divider()

# Scatter plots
st.subheader("📊 Planet Size vs Temperature (Discovery Facility)")
fig = px.scatter(
    df,
    x="pl_eqt",
    y="pl_rade",
    color="disc_facility",
    hover_name="pl_name",
    labels={
        "pl_eqt": "Equilibrium Temperature (K)",
        "pl_rade": "Planet Radius (Earth radii)",
        "disc_facility": "Discovery Facility"
    }
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Planet Size vs Temperature (Colored by Habitability)")
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
