import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AstroBioChem Explorer", layout="wide")

st.title("Hunter's AstroBioChem Explorer")
# Sidebar explanation
st.sidebar.title("🧪 Habitability Score")
st.sidebar.write("""
Score (0–100) based on:
- Temperature: 250–350 K → good
- Planet radius: 0.5–2.0 Earth radii → rocky & habitable
- Stellar type: G, K, quiet M → better
- Atmosphere: H₂O / CO₂ presence → bonus points

Formula is simple sum of normalized factors, scaled to 100.
""")

st.write("Exploring real NASA exoplanet data 🌍🪐")

st.divider()

# ---------------------------
# Load NASA Exoplanet Data
# ---------------------------

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
# Habitability scoring function
def habitability_score(row):
    score = 0
    
    # 1️⃣ Temperature (250–350 K ideal)
    if pd.notnull(row["pl_eqt"]):
        if 250 <= row["pl_eqt"] <= 350:
            score += 30
        else:
            score += max(0, 30 - abs(row["pl_eqt"]-300)/5)  # decreasing score if outside ideal

    # 2️⃣ Planet radius (0.5–2.0 Earth radii ideal)
    if pd.notnull(row["pl_rade"]):
        if 0.5 <= row["pl_rade"] <= 2.0:
            score += 30
        else:
            score += max(0, 30 - abs(row["pl_rade"]-1.25)*15)  # penalty if too big/small

    # 3️⃣ Stellar type (G, K, quiet M)
    # Using proxy: star temp as proxy for type
    if pd.notnull(row["st_teff"]):
        if 3700 <= row["st_teff"] <= 5200:  # K + M
            score += 20
        elif 5200 < row["st_teff"] <= 6000:  # G stars
            score += 20
        # else no points

    # 4️⃣ Atmosphere presence (if known, optional)
    # NASA CSV may not have this, placeholder example:
    score += 0  # for now, we can extend later

    # Clip to 100
    return min(score, 100)

df = load_exoplanet_data()
# Create habitability column
df["habitability"] = df.apply(habitability_score, axis=1)


st.subheader("🔍 Exoplanet Dataset with Habitability Score")

search = st.text_input("Search by planet or star name:")

if search:
    filtered_df = df[
        df["pl_name"].str.contains(search, case=False, na=False) |
        df["hostname"].str.contains(search, case=False, na=False)
    ]
else:
    filtered_df = df

# Sort by habitability descending
filtered_df = filtered_df.sort_values(by="habitability", ascending=False)

st.dataframe(filtered_df, use_container_width=True)


st.divider()

# ---------------------------
# Plotly Scatter Plot
# ---------------------------

st.subheader("📊 Planet Size vs Temperature")

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

