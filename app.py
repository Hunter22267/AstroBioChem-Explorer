import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AstroBioChem Explorer", layout="wide")

st.title("Hunter's AstroBioChem Explorer")
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

df = load_exoplanet_data()

st.subheader("🔍 Exoplanet Dataset")
st.write("Data source: NASA Exoplanet Archive")

# ---------------------------
# Searchable Table
# ---------------------------

search = st.text_input("Search by planet or star name:")

if search:
    filtered_df = df[
        df["pl_name"].str.contains(search, case=False, na=False) |
        df["hostname"].str.contains(search, case=False, na=False)
    ]
else:
    filtered_df = df

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
