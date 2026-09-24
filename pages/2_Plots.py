import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Reservoir Plots")

# Read dataset using Streamlit caching

@st.cache_data
def load_data():

    df = pd.read_csv("data/reservoirs.csv")

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

# Convert date column to datetime format

    df["date"] = pd.to_datetime(df["date"])

    return df


df = load_data()

# Variables available for plotting

plot_columns = [
    "filling_ratio",
    "capacity_TWh",
    "stored_energy_TWh",
    "previous_week_filling_ratio",
    "filling_ratio_change"
]

# Sort data by date

df = df.sort_values(by="date")

# Aggregate values across all reservoir areas by date

df_plot = (
    df.groupby("date")[plot_columns]
      .mean()
      .reset_index()
)

# Allow user to select a variable

selected_column = st.selectbox(
    "Choose variable",
    ["All"] + plot_columns
)

# Allow user to select a month range
months = sorted(
    df_plot["date"].dt.to_period("M").astype(str).unique()
)

selected_range = st.select_slider(
    "Select month range",
    options=months,
    value=(months[0], months[0])
)

start_month, end_month = selected_range

filtered_df = df_plot[
    (df_plot["date"].dt.to_period("M").astype(str) >= start_month)
    &
    (df_plot["date"].dt.to_period("M").astype(str) <= end_month)
]

# # Create plot figure

fig, ax = plt.subplots(figsize=(12, 6))

if selected_column == "All":

    # Normalize variables to a common 0-1 scale
    normalized_df = filtered_df.copy()

    for col in plot_columns:
        normalized_df[col] = (
            normalized_df[col] - normalized_df[col].min()
        ) / (
            normalized_df[col].max() - normalized_df[col].min()
        )

    for col in plot_columns:
        ax.plot(
            normalized_df["date"],
            normalized_df[col],
            label=col
        )

    ax.set_title("Normalized Reservoir Data")
    ax.set_ylabel("Normalized Value (0-1)")

    st.info(
        "When 'All' is selected, the variables are normalized to a "
        "common scale (0-1) because they have different units and ranges."
    )

else:

    ax.plot(
        filtered_df["date"],
        filtered_df[selected_column],
        label=selected_column
    )

    ax.set_title(f"{selected_column} Over Time")
    ax.set_ylabel(selected_column)

ax.set_xlabel("Date")
ax.grid(True)
ax.legend()

st.pyplot(fig)