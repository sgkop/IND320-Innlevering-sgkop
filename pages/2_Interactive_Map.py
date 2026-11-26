import streamlit as st
import requests
import geopandas as gpd
import pandas as pd
import plotly.express as px
import os
import folium

from shapely.geometry import Polygon
from utils.area_coordinates import AREA_COORDINATES
from streamlit_folium import st_folium
from utils.theme import PLOTLY_TEMPLATE

# --------------------------------------------------------
# SESSION STATE SAFETY
# --------------------------------------------------------

if "area_type" not in st.session_state:
    st.session_state.area_type = "EL"

if "area_number" not in st.session_state:
    st.session_state.area_number = 1

# --------------------------------------------------------
# PAGE
# --------------------------------------------------------

st.title("Interactive Map")

st.info(
    """
    This page visualises Magasinstatistikk areas.

    The map currently focuses on the Norwegian
    electricity areas (NO1–NO5) used throughout
    the application.
    """
)

# --------------------------------------------------------
# CURRENT SELECTION
# --------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Area Type",
        st.session_state.area_type
    )

with col2:
    st.metric(
        "Area Number",
        st.session_state.area_number
    )

# --------------------------------------------------------
# CONTROLS
# --------------------------------------------------------

selected_date = st.date_input(
    "Select Date"
)

st.session_state.selected_date = selected_date

map_property = st.selectbox(
    "Map Property",
    [
        "Reservoir Filling",
        "Temperature",
        "Precipitation"
    ]
)

st.session_state.map_property = map_property

# --------------------------------------------------------
# GEOMETRY
# --------------------------------------------------------

@st.cache_data
def load_elspot_geometry():

    url = (
        "https://kart.nve.no/enterprise/rest/services/"
        "Nettomraader/MapServer/0/query"
    )

    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": True,
        "f": "json"
    }

    data = requests.get(
        url,
        params=params
    ).json()

    records = []

    for feature in data["features"]:

        attrs = feature["attributes"]

        polygon = Polygon(
            feature["geometry"]["rings"][0]
        )

        attrs["geometry"] = polygon

        records.append(attrs)

    gdf = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs="EPSG:25833"
    )

    return gdf

# --------------------------------------------------------
# RESERVOIR DATA
# --------------------------------------------------------

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

@st.cache_data
def load_weather_summary(
    latitude,
    longitude,
    selected_date
):
    """
    Weather summary up to selected map date.
    """

    end_date = pd.Timestamp(
        selected_date
    )

    start_date = end_date - pd.Timedelta(
        days=365
    )

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.strftime(
            "%Y-%m-%d"
        ),
        "end_date": end_date.strftime(
            "%Y-%m-%d"
        ),
        "daily": [
            "temperature_2m_mean",
            "precipitation_sum"
        ],
        "timezone": "auto"
    }

    data = requests.get(
        url,
        params=params
    ).json()

    weather_df = pd.DataFrame(
        {
            "temperature": data["daily"][
                "temperature_2m_mean"
            ],
            "precipitation": data["daily"][
                "precipitation_sum"
            ]
        }
    )

    return {
        "temperature": weather_df[
            "temperature"
        ].mean(),

        "precipitation": weather_df[
            "precipitation"
        ].sum()
    }

# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------

with st.spinner(
    "Loading electricity areas..."
):
    regions_gdf = load_elspot_geometry()

regions_gdf = regions_gdf.to_crs(
    epsg=4326
)

reservoir_df = load_reservoir_data()

reservoir_df["dato_Id"] = pd.to_datetime(
    reservoir_df["dato_Id"]
)


# --------------------------------------------------------
# GEOJSON EXPORT
# --------------------------------------------------------

os.makedirs(
    "data/geojson",
    exist_ok=True
)

geojson_path = (
    "data/geojson/elspot_areas.geojson"
)

regions_gdf.to_file(
    geojson_path,
    driver="GeoJSON"
)

# --------------------------------------------------------
# MAP VALUES
# --------------------------------------------------------

value_mapping = {}

selected_timestamp = pd.Timestamp(
    selected_date
)

# ---------------------------------
# Reservoir Filling
# ---------------------------------

if map_property == "Reservoir Filling":

    filtered_el = reservoir_df[
        (reservoir_df["omrType"] == "EL")
        &
        (
            reservoir_df["dato_Id"]
            <= selected_timestamp
        )
    ].copy()

    filtered_el = filtered_el.sort_values(
        "dato_Id"
    )

    latest_el = (
        filtered_el
        .groupby("omrnr")
        .tail(1)
    )

    for _, row in latest_el.iterrows():

        value_mapping[
            f"NO {int(row['omrnr'])}"
        ] = row["fyllingsgrad"]

# ---------------------------------
# Temperature
# ---------------------------------

elif map_property == "Temperature":

    for area in [1, 2, 3, 4, 5]:

        summary = load_weather_summary(
            *AREA_COORDINATES[
                ("EL", area)
            ],
            selected_date
        )

        value_mapping[
            f"NO {area}"
        ] = summary["temperature"]

# ---------------------------------
# Precipitation
# ---------------------------------

elif map_property == "Precipitation":

    for area in [1, 2, 3, 4, 5]:

        summary = load_weather_summary(
            *AREA_COORDINATES[
                ("EL", area)
            ],
            selected_date
        )

        value_mapping[
            f"NO {area}"
        ] = summary["precipitation"]

regions_gdf["display_value"] = (
    regions_gdf["budomr"]
    .map(value_mapping)
)

# --------------------------------------------------------
# SELECTED AREA MARKING
# --------------------------------------------------------

regions_gdf["selected"] = (
    regions_gdf["budomr"]
    ==
    f"NO {st.session_state.area_number}"
)

# --------------------------------------------------------
# MAP
# --------------------------------------------------------

fig = px.choropleth(
    regions_gdf,
    geojson=regions_gdf.geometry.__geo_interface__,
    locations=regions_gdf.index,
    color="display_value",
    hover_name="budomr",
    projection="mercator",
    template=PLOTLY_TEMPLATE
)

fig.update_traces(
    marker_line_width=1,
    marker_line_color="white"
)

fig.update_geos(
    fitbounds="locations",
    visible=False
)

fig.update_layout(
    title=f"{map_property} by Electricity Area",
    coloraxis_colorbar_title=map_property,
    margin={
        "r": 0,
        "t": 50,
        "l": 0,
        "b": 0
    }
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ----------------------------------------
# SELECTED AREA INFO
# ----------------------------------------

st.info(
    f"Selected area: "
    f"EL / {st.session_state.area_number}"
)

# --------------------------------------------------------
# AREA SELECTION
# --------------------------------------------------------

area_options = [
    "NO 1",
    "NO 2",
    "NO 3",
    "NO 4",
    "NO 5"
]

selected_area = st.selectbox(
    "Select Area",
    area_options,
    index=int(
        max(
            min(
                st.session_state.area_number - 1,
                len(area_options) - 1
            ),
            0
        )
    )
)

selected_number = int(
    selected_area.replace(
        "NO ",
        ""
    )
)

if st.button(
    "Use Selected Area"
):

    st.session_state.area_type = "EL"

    st.session_state.area_number = (
        selected_number
    )

    st.success(
        f"Selected EL/{selected_number}"
    )

#--------------------------------------------------------
# Folium MAP
#--------------------------------------------------------

st.subheader("Interactive Area Selection")

m = folium.Map(
    location=[64, 12],
    zoom_start=4,
    tiles="OpenStreetMap"
)

geojson_data = regions_gdf.to_json()

folium.GeoJson(
    geojson_data,
    tooltip=folium.GeoJsonTooltip(
        fields=["budomr"]
    ),
    highlight_function=lambda feature: {
        "weight": 6,
        "color": "red"
    }
).add_to(m)

map_data = st_folium(
    m,
    width=900,
    height=500
)

if (
    map_data
    and
    map_data.get(
        "last_active_drawing"
    )
):

    properties = map_data[
        "last_active_drawing"
    ][
        "properties"
    ]

    clicked_area = properties.get(
        "budomr"
    )

    if clicked_area:

        selected_number = int(
            clicked_area.replace(
                "NO ",
                ""
            )
        )

        if (
            selected_number
            !=
            st.session_state.area_number
        ):

            st.session_state.area_type = "EL"

            st.session_state.area_number = (
                selected_number
            )

            st.rerun()
