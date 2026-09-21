import streamlit as st

st.set_page_config(
    page_title="Reservoir Dashboard",
    layout="wide"
)

st.title("Reservoir Dashboard")

st.write(
    """
    Welcome to the reservoir dashboard.

    Use the navigation menu on the left to navigate between pages.
    """
)

st.sidebar.success("Choose a page.")