import streamlit as st
import pandas as pd

st.title("Data Table")


@st.cache_data
def load_data():
    return pd.read_csv("data/reservoirs.csv")


df = load_data()

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

# Lag én rad per kolonne
column_data = []

for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        values = df[col].head(30).tolist()
    else:
        values = []

    column_data.append({
        "Column": col,
        "First Month": values
    })

table_df = pd.DataFrame(column_data)

st.dataframe(
    table_df,
    column_config={
        "First Month": st.column_config.LineChartColumn(
            "First Month",
            help="First month of values"
        )
    },
    use_container_width=True
)
