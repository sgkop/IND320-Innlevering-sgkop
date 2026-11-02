import streamlit as st

st.set_page_config(
    page_title="Energy Data Dashboard",
    layout="wide"
)

st.title("Energy Data Dashboard")

st.write(
    """
    Welcome to the Energy Data Dashboard.

    The application contains analyses and visualisations
    based on reservoir statistics from NVE, historical
    weather data from Open-Meteo, and cross-border
    electricity flow data from ENTSO-E.

    Available functionality includes:

    • Reservoir data exploration

    • Interactive plots

    • Cross-border flow analysis

    • STL decomposition

    • Spectrogram analysis

    • SPC outlier detection

    • LOF anomaly detection

    Use the navigation menu on the left to explore
    the available pages.
    """
)