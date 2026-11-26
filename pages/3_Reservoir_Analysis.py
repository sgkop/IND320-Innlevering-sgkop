import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.graph_objects as go

from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram
from utils.theme import PLOTLY_TEMPLATE

# --------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------

@st.cache_data
def load_reservoir_data():
    """
    Download public reservoir statistics from
    Magasinstatistikk API.

    The dataset contains weekly observations for:
    - EL (price areas)
    - VASS (watercourse regions)
    - NO (Norway total)

    The data are reused throughout the Streamlit app.
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
# STL DECOMPOSITION
# --------------------------------------------------------

def stl_analysis(
    series,
    seasonal=53,
    trend=105,
    robust=True
):
    """
    Perform STL decomposition.
    """

    stl = STL(
        series,
        seasonal=seasonal,
        trend=trend,
        robust=robust
    )

    return stl.fit()


# --------------------------------------------------------
# SPECTROGRAM ANALYSIS
# --------------------------------------------------------

def spectrogram_analysis(
    series,
    window_length=128,
    overlap=64
):
    """
    Compute a spectrogram representation of the
    reservoir filling time series.
    """

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

st.info(
    """
    This page presents STL decomposition and
    spectrogram analysis of reservoir filling data
    from NVE Magasinstatistikk.

    The selected area is shared with the rest of the
    application through Streamlit session state.
    """
)

# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------

df = load_reservoir_data()

area_type = st.session_state.area_type
area_number = st.session_state.area_number

st.caption(
    f"""
    Selected area:
    {area_type} / {area_number}
    """
)

# --------------------------------------------------------
# FILTER DATA
# --------------------------------------------------------

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

# --------------------------------------------------------
# PAGE TABS
# --------------------------------------------------------

tab1, tab2 = st.tabs(
    [
        "STL Analysis",
        "Spectrogram"
    ]
)

# ========================================================
# STL ANALYSIS
# ========================================================

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
        "Advanced Settings"
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

    # Perform STL decomposition
    result = stl_analysis(
        series,
        seasonal=seasonal,
        trend=trend,
        robust=robust
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=series.values,
            name="Original",
            mode="lines"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=result.trend,
            name="Trend",
            mode="lines"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=result.seasonal,
            name="Seasonal",
            mode="lines"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=series.index,
            y=result.resid,
            name="Residual",
            mode="lines"
        )
    )

    fig.update_layout(
        title="STL Decomposition",
        xaxis_title="Date",
        yaxis_title="Filling Degree (%)",
        template=PLOTLY_TEMPLATE
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        f"Seasonal={seasonal} | "
        f"Trend={trend} | "
        f"Robust={robust}"
    )

# ========================================================
# SPECTROGRAM
# ========================================================

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

            Stronger colours indicate stronger periodic
            behaviour in the reservoir filling series.
            """
        )

    window_length = 128
    overlap = 64

    with st.expander(
        "Advanced Settings"
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

        spectrum_db = (
            10 * np.log10(
                spectrum + 1e-12
            )
        )

        fig = go.Figure(
            data=
            go.Heatmap(
                z=spectrum_db,
                x=times,
                y=frequencies,
                colorscale="Viridis",
                colorbar=dict(
                    title="dB"
                )
            )
        )

        fig.update_layout(
            title="Spectrogram of Reservoir Filling",
            xaxis_title="Time Window",
            yaxis_title="Frequency",
            template=PLOTLY_TEMPLATE
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.caption(
            f"Window length={window_length} | "
            f"Overlap={overlap}"
        )