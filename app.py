import streamlit as st

st.set_page_config(
    page_title="Energy Data Dashboard",
    layout="wide"
)

st.title("Energy Data Dashboard")

st.write(
    """
    Welcome to the Energy Data Dashboard.

    The application contains visualisations based on
    reservoir statistics from NVE and cross-border
    electricity flow data from ENTSO-E.

    Use the navigation menu on the left to explore
    the available pages.
    """
)