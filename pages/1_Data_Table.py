import streamlit as st
import pandas as pd
import requests

st.title("Reservoir Data Table")

# Read data from the NVE Magasinstatistikk API
@st.cache_data
def load_data():

    url = (
        "https://biapi.nve.no/magasinstatistikk/api/"
        "Magasinstatistikk/HentOffentligData"
    )

    data = requests.get(url).json()

    df = pd.DataFrame(data)

    # Rename Norwegian column names to English
    df = df.rename(columns={
        "dato_Id": "date",
        "omrType": "area_type",
        "omrnr": "area_number",
        "iso_aar": "year",
        "iso_uke": "week",
        "fyllingsgrad": "filling_ratio",
        "kapasitet_TWh": "capacity_TWh",
        "fylling_TWh": "stored_energy_TWh",
        "neste_Publiseringsdato": "next_publication_date",
        "fyllingsgrad_forrige_uke": "previous_week_filling_ratio",
        "endring_fyllingsgrad": "filling_ratio_change"
    })

    # Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])

    return df


df = load_data()

# Select area type
area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"]
)

# Filter to selected area type
filtered_df = df[
    df["area_type"] == area_type
]

# Select area number
area_number = st.selectbox(
    "Area number",
    sorted(filtered_df["area_number"].unique())
)

# Filter to selected area number
filtered_df = filtered_df[
    filtered_df["area_number"] == area_number
]

# Sort chronologically
filtered_df = (
    filtered_df
    .sort_values("date")
    .reset_index(drop=True)
)

st.subheader(
    f"Reservoir statistics for {area_type}-{area_number}"
)

# Variables displayed as mini line charts
numeric_columns = [
    "filling_ratio",
    "capacity_TWh",
    "stored_energy_TWh",
    "previous_week_filling_ratio",
    "filling_ratio_change"
]

column_data = []

for col in numeric_columns:

    values = (
        filtered_df[col]
        .head(30)
        .tolist()
    )

    column_data.append({
        "Variable": col,
        "First Month": values
    })

table_df = pd.DataFrame(column_data)

# Display mini charts
st.dataframe(
    table_df,
    column_config={
        "First Month": st.column_config.LineChartColumn(
            "First Month",
            help="First observations in chronological order"
        )
    },
    use_container_width=True
)

# Show filtered dataset
with st.expander("View filtered dataset"):

    st.dataframe(
        filtered_df,
        use_container_width=True
    )