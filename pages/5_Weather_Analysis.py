import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt

from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor

st.title("Weather Analysis")

st.info(
    """
    This page presents the SPC and LOF analyses
    developed and tested in the Jupyter Notebook
    using weather data retrieved through the
    Open-Meteo ERA5 reanalysis service.
    """
)

st.caption(
    "Weather dataset: NO3 / Region Midt-Norge (2024)"
)


@st.cache_data
def load_weather():

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
    )

    params = {
        "latitude": 63.25,
        "longitude": 9.90,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "hourly": [
            "temperature_2m",
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
        .agg({
            "temperature_2m": "mean",
            "precipitation": "sum"
        })
    )

# Load Open-Meteo weather data used for SPC and LOF analysis

daily_weather = load_weather()

tab1, tab2 = st.tabs(
    [
        "SPC Analysis",
        "LOF Analysis"
    ]
)

# --------------------------------------------------------
# SPC
# --------------------------------------------------------

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
            precipitation events.

            Seasonal variation is removed using
            a Discrete Cosine Transform (DCT)
            before outlier detection.

            Red markers indicate observations
            classified as outliers.
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
        daily_weather["precipitation"]
        .values
    )

    # Remove low-frequency seasonal variation before SPC analysis
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

    median = np.median(
        satv
    )

    # Estimate robust SPC limits using Median Absolute Deviation
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

    # Identify precipitation outliers
    outliers = (
        (satv > upper_limit)
        |
        (satv < lower_limit)
    )

    st.metric(
        "Outliers",
        int(outliers.sum())
    )

    fig, ax = plt.subplots(
        figsize=(10, 4)
    )

    ax.plot(
        daily_weather.index,
        signal,
        label="Precipitation"
    )

    ax.scatter(
        daily_weather.index[outliers],
        signal[outliers],
        color="red",
        label="Outliers"
    )

    ax.axhline(
        upper_limit,
        color="red",
        linestyle="--"
    )

    ax.set_title(
        "SPC Analysis of Precipitation"
    )

    ax.legend()

    st.pyplot(fig)

    st.caption(
        f"DCT cutoff = {dct_cutoff}, "
        f"Standard deviations = {n_std}"
    )

# --------------------------------------------------------
# LOF
# --------------------------------------------------------

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
            surrounding observations.

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
        daily_weather["temperature_2m"]
        .values
        .reshape(-1, 1)
    )

    # Detect temperature anomalies using Local Outlier Factor
    lof = LocalOutlierFactor(
        contamination=contamination
    )

    labels = lof.fit_predict(
        values
    )

    # Flag observations classified as anomalies
    anomalies = (
        labels == -1
    )

    st.metric(
        "Anomalies",
        int(anomalies.sum())
    )

    fig, ax = plt.subplots(
        figsize=(10, 4)
    )

    ax.plot(
        daily_weather.index,
        daily_weather["temperature_2m"],
        label="Temperature"
    )

    ax.scatter(
        daily_weather.index[anomalies],
        daily_weather["temperature_2m"][anomalies],
        color="red",
        label="Anomalies"
    )

    ax.set_title(
        "LOF Analysis of Temperature"
    )

    ax.legend()

    st.pyplot(fig)

    st.caption(
        f"Contamination = {contamination:.3f}"
    )