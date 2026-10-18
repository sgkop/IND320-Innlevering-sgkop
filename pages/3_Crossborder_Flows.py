import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from pymongo import MongoClient

st.title("ENTSO-E Crossborder Flows")

# Connect to MongoDB
uri = st.secrets["MONGO_URI"]

client = MongoClient(uri)

db = client["ind320"]
collection = db["crossborder_flows"]

# Load data from MongoDB
records = list(
    collection.find({}, {"_id": 0})
)

df = pd.DataFrame(records)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

# Consistent colors across all plots
color_map = {
    "NO_to_DK": "tab:blue",
    "DK_to_NO": "tab:orange"
}

# Layout
left_col, right_col = st.columns(2)

with left_col:

    connection = st.radio(
        "Connection",
        sorted(df["connection"].unique())
    )

    year = st.selectbox(
        "Year",
        sorted(
            df["timestamp"]
            .dt.year
            .unique()
        )
    )

    pie_df = df[
        (df["connection"] == connection)
        &
        (df["timestamp"].dt.year == year)
    ]

    pie_data = (
        pie_df
        .groupby("direction")["flow_mw"]
        .sum()
    )

    # Match colors to labels
    pie_colors = [
        color_map[label]
        for label in pie_data.index
    ]

    fig1, ax1 = plt.subplots(
        figsize=(6, 6)
    )

    ax1.pie(
        pie_data.values,
        labels=pie_data.index,
        autopct="%1.1f%%",
        colors=pie_colors
    )

    ax1.set_title(
        f"{connection} ({year})"
    )

    st.pyplot(fig1)

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

    line_df = df[
        (df["connection"] == connection)
        &
        (df["timestamp"].dt.year == year)
    ]

    if selected_months:

        selected_month_numbers = [
            month_names.index(m) + 1
            for m in selected_months
        ]

        line_df = line_df[
            line_df["timestamp"]
            .dt.month
            .isin(selected_month_numbers)
        ]

    # Aggregate to daily averages
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

    fig2, ax2 = plt.subplots(
        figsize=(8, 5)
    )

    for direction in daily_df["direction"].unique():

        subset = daily_df[
            daily_df["direction"] == direction
        ]

        ax2.plot(
            subset["date"],
            subset["flow_mw"],
            label=direction,
            color=color_map[direction],
            linewidth=2
        )

    ax2.set_title(
        "Average Daily Flow"
    )

    ax2.set_xlabel(
        "Date"
    )

    ax2.set_ylabel(
        "Flow (MW)"
    )

    ax2.grid(True)

    ax2.legend()

    plt.tight_layout()

    st.pyplot(fig2)

with st.expander("Data source and workflow"):

    st.write(
        """
        Cross-border flow data were retrieved from the
        ENTSO-E API.

        The data were first stored in Cassandra,
        processed using Apache Spark,
        transferred to MongoDB Atlas,
        and finally accessed directly
        by this Streamlit application.

        The pie chart shows the annual energy
        exchange by direction, while the line chart
        displays average daily power flows for the
        selected months.
        """
    )