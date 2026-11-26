import streamlit as st
import pandas as pd
import plotly.express as px

from pymongo import MongoClient

# --------------------------------------------------------
# PAGE
# --------------------------------------------------------

st.title("Crossborder Flow Analysis")

st.info(
    """
    This page presents cross-border electricity
    exchange between Norway and neighbouring
    countries using data retrieved from the
    ENTSO-E API.

    The data were stored in MongoDB after collection
    and preprocessing in the notebook environment.
    """
)

with st.expander(
    "About Controls"
):
    st.markdown(
        """
        **Connection**

        Cross-border electricity connection included
        in the analysis.

        **Year**

        Year used in the aggregation.

        **Months**

        Select one or more months for detailed
        daily flow analysis.
        """
    )

# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------

uri = st.secrets["MONGO_URI"]

client = MongoClient(uri)

db = client["ind320"]

collection = db["crossborder_flows"]

records = list(
    collection.find(
        {},
        {"_id": 0}
    )
)

df = pd.DataFrame(
    records
)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

# --------------------------------------------------------
# CONSISTENT COLORS
# --------------------------------------------------------

FLOW_COLORS = {
    "NO_to_DK": "#1f77b4",
    "DK_to_NO": "#ff7f0e"
}

# --------------------------------------------------------
# CONTROLS
# --------------------------------------------------------

left_col, right_col = st.columns(2)

connections = sorted(
    df["connection"].unique()
)

with left_col:

    if len(connections) == 1:

        connection = connections[0]

        st.info(
            f"Connection: {connection}"
        )

    else:

        connection = st.radio(
            "Connection",
            connections
        )

    year = st.selectbox(
        "Year",
        sorted(
            df["timestamp"]
            .dt.year
            .unique()
        )
    )

with right_col:

    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

    selected_months = st.pills(
        "Months",
        month_names,
        selection_mode="multi"
    )

# --------------------------------------------------------
# DATA FILTERING
# --------------------------------------------------------

filtered_df = df[
    (df["connection"] == connection)
    &
    (df["timestamp"].dt.year == year)
].copy()

# --------------------------------------------------------
# PIE CHART DATA
# --------------------------------------------------------

pie_data = (
    filtered_df
    .groupby("direction")["flow_mw"]
    .sum()
    .reset_index()
)

# --------------------------------------------------------
# PIE CHART
# --------------------------------------------------------

fig_pie = px.pie(
    pie_data,
    values="flow_mw",
    names="direction",
    title=f"{connection} ({year})",
    color="direction",
    color_discrete_map=FLOW_COLORS
)

fig_pie.update_layout(
    template="plotly_white"
)

# --------------------------------------------------------
# LINE CHART DATA
# --------------------------------------------------------

line_df = filtered_df.copy()

if selected_months:

    selected_month_numbers = [
        month_names.index(month) + 1
        for month in selected_months
    ]

    line_df = line_df[
        line_df["timestamp"]
        .dt.month
        .isin(selected_month_numbers)
    ]

line_df["date"] = (
    line_df["timestamp"]
    .dt.date
)

daily_df = (
    line_df
    .groupby(
        ["date", "direction"]
    )["flow_mw"]
    .mean()
    .reset_index()
)

daily_df["date"] = pd.to_datetime(
    daily_df["date"]
)

complete_frames = []

for direction in daily_df["direction"].unique():

    subset = (
        daily_df[
            daily_df["direction"] == direction
        ]
        .set_index("date")
    )

    full_index = pd.date_range(
        subset.index.min(),
        subset.index.max(),
        freq="D"
    )

    subset = subset.reindex(
        full_index
    )

    subset["direction"] = direction

    subset = subset.reset_index()

    subset = subset.rename(
        columns={
            "index": "date"
        }
    )

    complete_frames.append(
        subset
    )

daily_df = pd.concat(
    complete_frames,
    ignore_index=True
)

daily_df = (
    daily_df
    .sort_values("date")
)

# --------------------------------------------------------
# LINE CHART
# --------------------------------------------------------

fig_line = px.line(
    daily_df,
    x="date",
    y="flow_mw",
    color="direction",
    color_discrete_map=FLOW_COLORS,
    title="Average Daily Flow"
)

fig_line.update_layout(
    template="plotly_white",
    xaxis_title="Date",
    yaxis_title="Flow (MW)"
)

fig_line.update_traces(
    connectgaps=False
)

# --------------------------------------------------------
# DISPLAY
# --------------------------------------------------------

plot_col1, plot_col2 = st.columns(2)

with plot_col1:

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

with plot_col2:

    st.plotly_chart(
        fig_line,
        use_container_width=True
    )

# --------------------------------------------------------
# DATA SOURCE DOCUMENTATION
# --------------------------------------------------------

with st.expander(
    "Data Source and Workflow"
):

    st.markdown(
        """
        Cross-border flow data were retrieved from
        the ENTSO-E API.

        The data were:

        1. Collected from ENTSO-E
        2. Stored in Cassandra
        3. Processed using Apache Spark
        4. Transferred to MongoDB Atlas
        5. Accessed directly by this Streamlit app

        The pie chart displays total yearly energy
        exchange by direction.

        The line chart displays average daily power
        flow for the selected months.
        """
    )