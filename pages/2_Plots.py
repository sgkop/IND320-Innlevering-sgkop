import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.title("Reservoir Plots")


# Load data from NVE API
@st.cache_data
def load_data():

    url = (
        "https://biapi.nve.no/magasinstatistikk/api/"
        "Magasinstatistikk/HentOffentligData"
    )

    data = requests.get(url).json()

    df = pd.DataFrame(data)

    # Rename Norwegian column names
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

    df["date"] = pd.to_datetime(df["date"])

    return df


df = load_data()

# Select area type
area_type = st.radio(
    "Area type",
    ["EL", "NO", "VASS"]
)

# Filter area type
filtered_df = df[
    df["area_type"] == area_type
]

# Select area number
area_number = st.selectbox(
    "Area number",
    sorted(filtered_df["area_number"].unique())
)

# Filter area number
filtered_df = filtered_df[
    filtered_df["area_number"] == area_number
]

# Sort chronologically
filtered_df = (
    filtered_df
    .sort_values("date")
    .reset_index(drop=True)
)

# Variables available for plotting
plot_columns = [
    "filling_ratio",
    "capacity_TWh",
    "stored_energy_TWh",
    "previous_week_filling_ratio",
    "filling_ratio_change"
]

selected_column = st.selectbox(
    "Choose variable",
    ["All"] + plot_columns
)

# Month slider
months = sorted(
    filtered_df["date"]
    .dt.to_period("M")
    .astype(str)
    .unique()
)

selected_range = st.select_slider(
    "Select month range",
    options=months,
    value=(months[0], months[-1])
)

start_month, end_month = selected_range

plot_df = filtered_df[
    (
        filtered_df["date"]
        .dt.to_period("M")
        .astype(str)
        >= start_month
    )
    &
    (
        filtered_df["date"]
        .dt.to_period("M")
        .astype(str)
        <= end_month
    )
]

fig, ax = plt.subplots(figsize=(12, 6))

if selected_column == "All":

    normalized_df = plot_df.copy()

    for col in plot_columns:

        if (
            normalized_df[col].max()
            != normalized_df[col].min()
        ):

            normalized_df[col] = (
                normalized_df[col]
                - normalized_df[col].min()
            ) / (
                normalized_df[col].max()
                - normalized_df[col].min()
            )

        else:

            normalized_df[col] = 0

    for col in plot_columns:

        ax.plot(
            normalized_df["date"],
            normalized_df[col],
            label=col
        )

    ax.set_title(
        f"Normalized variables for {area_type}-{area_number}"
    )

    ax.set_ylabel(
        "Normalized value (0-1)"
    )

    st.info(
        "When 'All' is selected, variables are normalized "
        "to a common scale because they have different units."
    )

else:

    ax.plot(
        plot_df["date"],
        plot_df[selected_column],
        label=selected_column,
        linewidth=2
    )

    ax.set_title(
        f"{selected_column} for {area_type}-{area_number}"
    )

    ax.set_ylabel(
        selected_column
    )

ax.set_xlabel("Date")

ax.grid(True)

ax.legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

st.pyplot(fig)

# Optional data view
with st.expander("View filtered dataset"):

    st.dataframe(
        plot_df,
        use_container_width=True
    )