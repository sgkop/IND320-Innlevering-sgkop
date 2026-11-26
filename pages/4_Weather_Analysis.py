import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.graph_objects as go

from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor
from utils.area_coordinates import AREA_COORDINATES
from utils.theme import PLOTLY_TEMPLATE

# --------------------------------------------------------
# SESSION STATE SAFETY
# --------------------------------------------------------

if "area_type" not in st.session_state:
    st.session_state.area_type = "EL"

if "area_number" not in st.session_state:
    st.session_state.area_number = 1

# --------------------------------------------------------
# PAGE DESCRIPTION
# --------------------------------------------------------

st.title("Weather Analysis")

st.info(
    """
    This page presents the SPC and LOF analyses
    developed and tested in the Jupyter Notebook.

    Historical weather observations are downloaded
    from Open-Meteo ERA5 reanalysis.

    The selected area is shared with the rest of the
    application through Streamlit session state.
    """
)

# --------------------------------------------------------
# CURRENT AREA SELECTION
# --------------------------------------------------------

selected_type = st.session_state.area_type
selected_number = st.session_state.area_number

# Default coordinate (fallback)
lat = 63.25
lon = 9.90

# Retrieve representative coordinates for the
# currently selected Magasinstatistikk area.
if (
    selected_type,
    selected_number
) in AREA_COORDINATES:

    lat, lon = AREA_COORDINATES[
        (
            selected_type,
            selected_number
        )
    ]

st.caption(
    f"""
    Selected area:
    {selected_type} / {selected_number}

    Coordinates:
    ({lat:.2f}, {lon:.2f})
    """
)

# --------------------------------------------------------
# DATA DOWNLOAD
# --------------------------------------------------------

@st.cache_data
def load_weather(latitude, longitude):
    """
    Download historical weather observations from
    Open-Meteo ERA5 reanalysis.

    Data are aggregated to daily resolution because
    SPC and LOF analyses are performed on daily
    weather series.
    """

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "hourly": [
            "temperature",
            "precipitation"
        ]
    }

    weather_data = (
        requests.get(
            url,
            params=params
        ).json()
    )

    df = pd.DataFrame(
        weather_data["hourly"]
    )

    df["time"] = pd.to_datetime(
        df["time"]
    )

    return (
        df
        .set_index("time")
        .resample("D")
        .agg(
            {
                "temperature": "mean",
                "precipitation": "sum"
            }
        )
    )

# Retrieve weather observations for selected area.
daily_weather = load_weather(
    lat,
    lon
)

# --------------------------------------------------------
# WEATHER PROPERTY SELECTION
# --------------------------------------------------------

weather_property = st.selectbox(
    "Weather Variable",
    [
        "temperature",
        "precipitation"
    ],
    index=0
)

# --------------------------------------------------------
# PAGE TABS
# --------------------------------------------------------

tab1, tab2 = st.tabs(
    [
        "SPC Analysis",
        "LOF Analysis"
    ]
)

# ========================================================
# SPC ANALYSIS
# ========================================================

with tab1:

    st.subheader(
        "Statistical Process Control"
    )

    with st.expander(
        "About SPC Analysis"
    ):
        st.write(
            """
            Statistical Process Control (SPC)
            identifies unusually high or low
            weather observations.

            Seasonal variation is removed using a
            Discrete Cosine Transform (DCT) before
            robust control limits are estimated.

            Control limits are calculated from the
            seasonally adjusted SATV signal using
            robust statistics based on the Median
            Absolute Deviation (MAD).

            Only detected outliers are displayed
            on the original weather series.
            """
        )

    dct_cutoff = st.slider(
        "DCT Cutoff",
        min_value=1,
        max_value=100,
        value=20
    )

    n_std = st.slider(
        "Standard Deviations",
        min_value=1,
        max_value=5,
        value=3
    )

    signal = (
        daily_weather[weather_property]
        .values
    )

    # Remove low-frequency seasonal variation
    coeffs = dct(
        signal,
        norm="ortho"
    )

    filtered = coeffs.copy()

    filtered[:dct_cutoff] = 0

    satv = idct(
        filtered,
        norm="ortho"
    )

    # Robust centre estimate
    median = np.median(
        satv
    )

    # Robust spread estimate
    mad = np.median(
        np.abs(
            satv - median
        )
    )

    robust_std = (
        1.4826 * mad
    )

    upper_limit = (
        median
        + n_std * robust_std
    )

    lower_limit = (
        median
        - n_std * robust_std
    )

    # Detect outliers in SATV signal
    outliers = (
        (satv > upper_limit)
        |
        (satv < lower_limit)
    )

    st.metric(
        "Outliers",
        int(outliers.sum())
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_weather.index,
            y=signal,
            mode="lines",
            name=weather_property
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily_weather.index[outliers],
            y=np.array(signal)[outliers],
            mode="markers",
            name="Outliers",
            marker=dict(
                color="red",
                size=8
            )
        )
    )

    fig.update_layout(
        title=f"SPC Analysis of {weather_property}",
        xaxis_title="Date",
        yaxis_title=weather_property,
        template=PLOTLY_TEMPLATE
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        f"DCT cutoff = {dct_cutoff} | "
        f"Standard deviations = {n_std}"
    )

    st.info(
        """
        Outliers are identified using robust SPC
        limits estimated from the DCT-filtered SATV
        signal. Only the resulting outliers are shown
        on the original weather series.
        """
    )

# ========================================================
# LOF ANALYSIS
# ========================================================

with tab2:

    st.subheader(
        "Local Outlier Factor"
    )

    with st.expander(
        "About LOF Analysis"
    ):
        st.write(
            """
            Local Outlier Factor (LOF)
            identifies temperature observations
            that differ substantially from their
            neighbouring observations.

            Red markers indicate observations
            classified as anomalies.
            """
        )

    contamination = st.slider(
        "Contamination",
        min_value=0.001,
        max_value=0.05,
        value=0.01,
        step=0.001,
        format="%.3f"
    )

    values = (
        daily_weather[weather_property]
        .values
        .reshape(-1, 1)
    )

    lof = LocalOutlierFactor(
        contamination=contamination
    )

    labels = lof.fit_predict(
        values
    )

    anomalies = (
        labels == -1
    )

    st.metric(
        "Anomalies",
        int(anomalies.sum())
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_weather.index,
            y=daily_weather[weather_property],
            mode="lines",
            name=weather_property
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily_weather.index[anomalies],
            y=daily_weather[weather_property][anomalies],
            mode="markers",
            name=weather_property,
            marker=dict(
                color="red",
                size=8
            )
        )
    )

    fig.update_layout(
        title=f"LOF Analysis of {weather_property}",
        xaxis_title="Date",
        yaxis_title=weather_property,
        template=PLOTLY_TEMPLATE
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        f"Contamination = {contamination:.3f}"
    )