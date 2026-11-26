import streamlit as st
import pandas as pd
import requests

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Energy Data Dashboard",
    layout="wide"
)

# --------------------------------------------------
# LOAD AREA OPTIONS
# --------------------------------------------------

@st.cache_data
def load_area_options():

    url = (
        "https://biapi.nve.no/magasinstatistikk/api/"
        "Magasinstatistikk/HentOffentligData"
    )

    response = requests.get(url)

    return pd.DataFrame(
        response.json()
    )


area_df = load_area_options()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "area_type" not in st.session_state:

    st.session_state.area_type = sorted(
        area_df["omrType"].unique()
    )[0]

if "area_number" not in st.session_state:

    first_area = area_df[
        area_df["omrType"]
        ==
        st.session_state.area_type
    ]

    st.session_state.area_number = sorted(
        first_area["omrnr"].unique()
    )[0]

# --------------------------------------------------
# GLOBAL AREA SELECTOR
# --------------------------------------------------

with st.sidebar:

    st.header("Area Selection")

    st.session_state.area_type = st.selectbox(
        "Area Type",
        sorted(
            area_df["omrType"].unique()
        )
    )

    available_numbers = sorted(
        area_df[
            area_df["omrType"]
            ==
            st.session_state.area_type
        ]["omrnr"].unique()
    )

    if (
        st.session_state.area_number
        not in available_numbers
    ):

        st.session_state.area_number = (
            available_numbers[0]
        )

    st.session_state.area_number = st.selectbox(
        "Area Number",
        available_numbers
    )

    with st.expander(
        "Area Information"
    ):

        st.markdown(
            """
            **EL (Electricity Areas)**

            - EL/1 = NO1
            - EL/2 = NO2
            - EL/3 = NO3
            - EL/4 = NO4
            - EL/5 = NO5

            **VASS (Water Areas)**

            - VASS/1
            - VASS/2
            - VASS/3

            **NO**

            - NO/0 = Entire Norway
            """
        )

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

st.title(
    "Energy Data Dashboard"
)

st.markdown(
    """
    This application combines reservoir statistics,
    weather observations, correlation analysis,
    forecasting models and electricity data within
    a common analytical environment.

    ---
    
    ## Data Overview
    
    - Data Overview
    - Interactive Map
    
    Explore underlying datasets and geographical areas. 
    Displays raw data, summary plots and geographical information.

    ---
    
    ## Analysis
    
    - Reservoir Analysis
    - Weather Analysis
    - Correlation Analysis
    
    Investigate reservoir behaviour, weather patterns,
    anomalies and relationships between data sources. 
    Provides reservoir, weather and correlation analyses.

    ---
    
    ## Forecasting
    
    - Machine Learning Forecast
    
    Generate reservoir filling forecasts using a
    configurable lag-based machine learning model.
    Contains machine learning forecasting tools.

    ---
    
    ## Electricity
    
    - Crossborder Flows
    
    Explore Norwegian electricity exchange data from
    ENTSO-E and related market information.
    Provides ENTSO-E cross-border electricity flow analysis.
    """
)

st.info(
    f"""
    Current global selection

    • Area Type: {st.session_state.area_type}

    • Area Number: {st.session_state.area_number}
    """
)

st.success(
    """
    Area selections made in the sidebar are shared
    across Reservoir Analysis, Weather Analysis,
    Correlation Analysis, Forecasting and Map views
    through Streamlit Session State.
    """
)