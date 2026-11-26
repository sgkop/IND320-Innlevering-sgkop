import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

from utils.theme import PLOTLY_TEMPLATE


# --------------------------------------------------------
# PAGE
# --------------------------------------------------------

st.title("Correlation Analysis")

st.info(
    """
    This page investigates relationships between
    weather conditions and reservoir filling.

    Correlations can be analysed using different
    weather variables, lag values and rolling
    window lengths.
    """
)

# --------------------------------------------------------
# CURRENT AREA
# --------------------------------------------------------

st.subheader("Selected Area")

st.write(
    f"Area Type: {st.session_state.area_type}"
)

st.write(
    f"Area Number: {st.session_state.area_number}"
)

# --------------------------------------------------------
# AREA COORDINATES
# --------------------------------------------------------

# Representative coordinates used for weather retrieval.
# These can later be replaced by centroids extracted
# from GeoJSON polygons.

AREA_COORDINATES = {
    ("EL", 1): (59.91, 10.75),
    ("EL", 2): (58.15, 8.00),
    ("EL", 3): (63.25, 9.90),
    ("EL", 4): (68.50, 17.00),
    ("EL", 5): (60.40, 6.10),
    ("NO", 0): (61.00, 10.00),
    ("VASS", 1): (61.00, 8.00),
    ("VASS", 2): (63.00, 10.00),
    ("VASS", 3): (67.00, 15.00)
}

lat, lon = AREA_COORDINATES.get(
    (
        st.session_state.area_type,
        st.session_state.area_number
    ),
    (63.25, 9.90)
)

# --------------------------------------------------------
# USER CONTROLS
# --------------------------------------------------------

st.subheader("Correlation Settings")

weather_variable = st.selectbox(
    "Weather Variable",
    [
        "temperature",
        "precipitation"
    ]
)

lag = st.slider(
    "Lag (days)",
    min_value=-30,
    max_value=30,
    value=0
)

window_length = st.slider(
    "Rolling Window Length (days)",
    min_value=30,
    max_value=365,
    value=90
)

# --------------------------------------------------------
# RESERVOIR DATA
# --------------------------------------------------------

@st.cache_data
def load_reservoir_data():
    """
    Download Magasinstatistikk data.
    """

    url = (
        "https://biapi.nve.no/magasinstatistikk/api/"
        "Magasinstatistikk/HentOffentligData"
    )

    response = requests.get(url)

    return pd.DataFrame(
        response.json()
    )


# --------------------------------------------------------
# WEATHER DATA
# --------------------------------------------------------

@st.cache_data
def load_weather(
    latitude,
    longitude
):
    """
    Download daily weather observations from
    Open-Meteo.
    """

    weather_url = (
        "https://archive-api.open-meteo.com/v1/archive"
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2010-01-01",
        "end_date": "2024-12-31",
        "daily": [
            "temperature_2m_mean",
            "precipitation_sum"
        ],
        "timezone": "auto"
    }

    data = requests.get(
        weather_url,
        params=params
    ).json()

    weather_df = pd.DataFrame(
        {
            "dato_Id": pd.to_datetime(
                data["daily"]["time"]
            ),
            "temperature": data["daily"][
                "temperature_2m_mean"
            ],
            "precipitation": data["daily"][
                "precipitation_sum"
            ]
        }
    )

    return weather_df


# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------

reservoir_df = load_reservoir_data()

reservoir_df = reservoir_df[
    (
        reservoir_df["omrType"]
        ==
        st.session_state.area_type
    )
    &
    (
        reservoir_df["omrnr"]
        ==
        st.session_state.area_number
    )
].copy()

reservoir_df["dato_Id"] = pd.to_datetime(
    reservoir_df["dato_Id"]
)

reservoir_df = reservoir_df.sort_values(
    "dato_Id"
)

weather_df = load_weather(
    lat,
    lon
)

# --------------------------------------------------------
# DAILY INTERPOLATION
# --------------------------------------------------------

# Magasinstatistikk is weekly.
# Interpolation is used to align with daily
# weather observations.

reservoir_daily = (
    reservoir_df
    .set_index("dato_Id")
    [["fyllingsgrad"]]
    .resample("D")
    .interpolate()
    .reset_index()
)

# --------------------------------------------------------
# MERGE
# --------------------------------------------------------

merged_df = pd.merge(
    reservoir_daily,
    weather_df,
    on="dato_Id",
    how="inner"
)

# --------------------------------------------------------
# LAG
# --------------------------------------------------------

merged_df["shifted_weather"] = (
    merged_df[
        weather_variable
    ]
    .shift(lag)
)

# --------------------------------------------------------
# OVERALL CORRELATION
# --------------------------------------------------------

overall_corr = (
    merged_df["fyllingsgrad"]
    .corr(
        merged_df[
            "shifted_weather"
        ]
    )
)

st.metric(
    "Correlation",
    f"{overall_corr:.3f}"
)

# --------------------------------------------------------
# ROLLING CORRELATION
# --------------------------------------------------------

rolling_corr = (
    merged_df["fyllingsgrad"]
    .rolling(
        window_length
    )
    .corr(
        merged_df[
            "shifted_weather"
        ]
    )
)

# --------------------------------------------------------
# PLOTLY
# --------------------------------------------------------

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=merged_df["dato_Id"],
        y=rolling_corr,
        mode="lines",
        name="Rolling Correlation"
    )
)

fig.update_layout(
    title=(
        f"Rolling Correlation: "
        f"Filling Degree vs {weather_variable}"
    ),
    xaxis_title="Date",
    yaxis_title="Correlation",
    template=PLOTLY_TEMPLATE
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# --------------------------------------------------------
# SUMMARY
# --------------------------------------------------------

st.caption(
    f"""
    Area: {st.session_state.area_type}
    / {st.session_state.area_number}

    Weather Variable: {weather_variable}

    Lag: {lag} days

    Window Length: {window_length} days
    """
)