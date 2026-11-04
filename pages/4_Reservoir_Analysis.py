import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt

from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram


@st.cache_data
def load_reservoir_data():

    url = (
        "https://biapi.nve.no/magasinstatistikk/api/"
        "Magasinstatistikk/HentOffentligData"
    )

    response = requests.get(url)

    return pd.DataFrame(
        response.json()
    )


def stl_analysis(
    series,
    seasonal=53,
    trend=105,
    robust=True
):

    stl = STL(
        series,
        seasonal=seasonal,
        trend=trend,
        robust=robust
    )

    return stl.fit()


def spectrogram_analysis(
    series,
    window_length=128,
    overlap=64
):

    centered = (
        series.values
        - np.mean(series.values)
    )

    frequencies, times, spectrum = spectrogram(
        centered,
        nperseg=window_length,
        noverlap=overlap
    )

    return frequencies, times, spectrum


# --------------------------------------------------------
# PAGE
# --------------------------------------------------------

st.title("Reservoir Analysis")

df = load_reservoir_data()

area_type = st.selectbox(
    "Area Type",
    sorted(df["omrType"].unique())
)

area_number = st.selectbox(
    "Area Number",
    sorted(
        df[
            df["omrType"] == area_type
        ]["omrnr"].unique()
    )
)

filtered = df[
    (df["omrType"] == area_type)
    &
    (df["omrnr"] == area_number)
].copy()

filtered["dato_Id"] = pd.to_datetime(
    filtered["dato_Id"]
)

filtered = filtered.sort_values(
    "dato_Id"
)

series = (
    filtered
    .set_index("dato_Id")
    ["fyllingsgrad"]
)

tab1, tab2 = st.tabs(
    [
        "STL Analysis",
        "Spectrogram"
    ]
)

# --------------------------------------------------------
# STL
# --------------------------------------------------------

with tab1:

    st.subheader(
        "Seasonal-Trend Decomposition"
    )

    with st.expander(
        "About STL Analysis"
    ):

        st.write(
            """
            STL (Seasonal-Trend decomposition using LOESS)
            separates the reservoir filling series into:

            • Trend

            • Seasonal variation

            • Residual variation

            This helps identify long-term developments
            while separating recurring yearly patterns.
            """
        )

    seasonal = 53
    trend = 105
    robust = True

    with st.expander(
        "Advanced settings"
    ):

        seasonal = st.number_input(
            "Seasonal smoother",
            min_value=3,
            value=53,
            step=2
        )

        trend = st.number_input(
            "Trend smoother",
            min_value=5,
            value=105,
            step=2
        )

        robust = st.checkbox(
            "Robust estimation",
            value=True
        )

    result = stl_analysis(
        series,
        seasonal=seasonal,
        trend=trend,
        robust=robust
    )

    fig = result.plot()

    st.pyplot(fig)

    st.caption(
        f"Seasonal={seasonal} | "
        f"Trend={trend} | "
        f"Robust={robust}"
    )

# --------------------------------------------------------
# SPECTROGRAM
# --------------------------------------------------------

with tab2:

    st.subheader(
        "Spectral Analysis"
    )

    with st.expander(
        "About Spectrogram"
    ):

        st.write(
            """
            A spectrogram visualises how frequency
            components evolve over time.

            Stronger colours indicate stronger
            periodic behaviour in the reservoir
            filling series.
            """
        )

    window_length = 128
    overlap = 64

    with st.expander(
        "Advanced settings"
    ):

        window_length = st.number_input(
            "Window length",
            min_value=16,
            value=128,
            step=16
        )

        overlap = st.number_input(
            "Window overlap",
            min_value=0,
            max_value=window_length - 1,
            value=min(
                64,
                window_length - 1
            )
        )

    if overlap >= window_length:

        st.error(
            "Window overlap must be smaller than window length."
        )

    else:

        frequencies, times, spectrum = (
            spectrogram_analysis(
                series,
                window_length=window_length,
                overlap=overlap
            )
        )

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        ax.pcolormesh(
            times,
            frequencies,
            10 * np.log10(
                spectrum + 1e-12
            ),
            shading="gouraud"
        )

        ax.set_title(
            "Spectrogram of Reservoir Filling"
        )

        ax.set_xlabel(
            "Time Window"
        )

        ax.set_ylabel(
            "Frequency"
        )

        st.pyplot(fig)

        st.caption(
            f"Window length={window_length} | "
            f"Overlap={overlap}"
        )