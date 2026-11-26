import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --------------------------------------------------------
# PAGE
# --------------------------------------------------------

st.title("Data Overview")

st.info(
    """
    This page provides an overview of reservoir
    statistics retrieved directly from the NVE
    Magasinstatistikk API.

    Users may explore the raw data, compare
    variables and inspect trends for different
    geographical areas.
    """
)

# --------------------------------------------------------
# SESSION STATE SAFETY
# --------------------------------------------------------

if "area_type" not in st.session_state:
    st.session_state.area_type = "EL"

if "area_number" not in st.session_state:
    st.session_state.area_number = 1

# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------

@st.cache_data
def load_data():

    url = (
        "https://biapi.nve.no/magasinstatistikk/api/"
        "Magasinstatistikk/HentOffentligData"
    )

    data = requests.get(url).json()

    df = pd.DataFrame(data)

    df = df.rename(
        columns={
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
        }
    )

    df["date"] = pd.to_datetime(
        df["date"]
    )

    return df


df = load_data()

# --------------------------------------------------------
# AREA FILTER
# --------------------------------------------------------

area_type = st.session_state.area_type
area_number = st.session_state.area_number

filtered_df = df[
    (df["area_type"] == area_type)
    &
    (df["area_number"] == area_number)
].copy()

filtered_df = (
    filtered_df
    .sort_values("date")
    .reset_index(drop=True)
)

st.caption(
    f"Selected Area: {area_type} / {area_number}"
)

# --------------------------------------------------------
# TABS
# --------------------------------------------------------

tab1, tab2 = st.tabs(
    [
        "Data Table",
        "Plots"
    ]
)

# ========================================================
# DATA TABLE
# ========================================================

with tab1:

    st.subheader(
        "Variable Overview"
    )

    preview_columns = [
        "filling_ratio",
        "stored_energy_TWh",
        "previous_week_filling_ratio",
        "filling_ratio_change"
    ]

    column_data = []

    for col in preview_columns:

        values = (
            filtered_df[col]
            .head(30)
            .tolist()
        )

        column_data.append(
            {
                "Variable": col,
                "First Month": values
            }
        )

    table_df = pd.DataFrame(
        column_data
    )

    st.dataframe(
        table_df,
        column_config={
            "First Month":
            st.column_config.LineChartColumn(
                "First Month",
                help="First observations in chronological order"
            )
        },
        use_container_width=True
    )

    with st.expander(
        "View Data"
    ):

        st.dataframe(
            filtered_df,
            use_container_width=True
        )

# ========================================================
# PLOTS
# ========================================================

with tab2:

    st.subheader(
        "Reservoir Statistics"
    )

    with st.expander(
        "About Plots"
    ):
        st.markdown(
            """
            **Single Variable**

            Display one variable using its
            original scale.

            **All Variables**

            Variables are normalised to allow
            comparison of trends despite having
            different units and magnitudes.

            Capacity is omitted from the combined
            plot because it is nearly constant and
            contributes little additional insight.
            """
        )

    plot_columns = [
        "filling_ratio",
        "stored_energy_TWh",
        "previous_week_filling_ratio",
        "filling_ratio_change"
    ]

    selected_column = st.selectbox(
        "Variable",
        ["All"] + plot_columns
    )

    months = sorted(
        filtered_df["date"]
        .dt.to_period("M")
        .astype(str)
        .unique()
    )

    selected_range = st.select_slider(
        "Month Range",
        options=months,
        value=(
            months[0],
            months[-1]
        )
    )

    start_month, end_month = (
        selected_range
    )

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

    if selected_column == "All":

        normalized_df = plot_df.copy()

        for col in plot_columns:

            if (
                normalized_df[col].max()
                !=
                normalized_df[col].min()
            ):

                normalized_df[col] = (
                    (
                        normalized_df[col]
                        -
                        normalized_df[col].min()
                    )
                    /
                    (
                        normalized_df[col].max()
                        -
                        normalized_df[col].min()
                    )
                )

            else:

                normalized_df[col] = 0

        plot_ready = (
            normalized_df[
                ["date"] + plot_columns
            ]
            .melt(
                id_vars="date",
                var_name="Variable",
                value_name="Value"
            )
        )

        fig = px.line(
            plot_ready,
            x="date",
            y="Value",
            color="Variable",
            title=(
                f"Normalised Variables "
                f"for {area_type}-{area_number}"
            ),
            template="plotly_white"
        )

        st.info(
            """
            Variables are normalised to a common
            0–1 scale for comparison.
            """
        )

    else:

        fig = px.line(
            plot_df,
            x="date",
            y=selected_column,
            title=(
                f"{selected_column} "
                f"for {area_type}-{area_number}"
            ),
            template="plotly_white"
        )

    fig.update_layout(
        xaxis_title="Date"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )