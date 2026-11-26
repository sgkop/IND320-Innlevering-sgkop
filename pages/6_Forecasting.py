import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.graph_objects as go

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from utils.theme import PLOTLY_TEMPLATE
from utils.area_coordinates import AREA_COORDINATES

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

st.title("Forecasting")

st.info(
    """
    This page presents a lag-based machine learning
    forecast of reservoir filling.

    Users may select both model parameters and
    exogenous weather variables.
    """
)

# --------------------------------------------------------
# CURRENT AREA
# --------------------------------------------------------

selected_type = st.session_state.area_type
selected_number = st.session_state.area_number

st.subheader("Selected Area")

if "selected_date" in st.session_state:

    st.write(
        f"Map Date: {st.session_state.selected_date}"
    )

st.write(
    f"{selected_type} / {selected_number}"
)

# --------------------------------------------------------
# COORDINATES
# --------------------------------------------------------

lat = 63.25
lon = 9.90

if (
    selected_type,
    selected_number
) in AREA_COORDINATES:

    lat, lon = AREA_COORDINATES[
        (
            selected_type,
            selected_number
        )
    ]

# --------------------------------------------------------
# DATA SOURCES
# --------------------------------------------------------

st.subheader("Forecast Settings")

with st.expander(
    "About Forecast Settings"
):

    st.markdown(
        """
        **Mode**

        - Model Validation evaluates the model by comparing
          predictions against observed data.
        - Future Forecast generates predictions beyond the
          available observations.

        **History Length**

        Number of previous observations used for training.

        **Forecast Horizon**

        Number of future periods to predict.

        **Number of Trees**

        Controls Random Forest complexity. More trees may
        improve stability but increase training time.

        **Lag Features**

        Previous filling levels used as predictive inputs.

        **Weather Variables**

        Weather variables are optional exogenous predictors.

        If no weather variables are selected, forecasting is
        performed using lagged reservoir filling levels only.
        """
    )


forecast_mode = st.radio(
    "Mode",
    [
        "Model Validation",
        "Future Forecast"
    ],
    horizontal=True
)
    # --------------------------------------------------------
    # RESET RESULTS WHEN MODE CHANGES
    # --------------------------------------------------------

if (
    "forecast_mode" in st.session_state
    and
    st.session_state.forecast_mode
    != forecast_mode
):

    st.session_state.pop(
        "forecast_result",
        None
    )

    st.session_state.forecast_mode = (
        forecast_mode
    )

elif "forecast_mode" not in st.session_state:

    st.session_state.forecast_mode = (
        forecast_mode
    )

    #--------------------------------------------------------
    
history_length = st.slider(
    "History Length",
    min_value=52,
    max_value=520,
    value=260,
    step=52
)

forecast_horizon = st.slider(
    "Forecast Horizon",
    min_value=4,
    max_value=26,
    value=12
)

n_estimators = st.slider(
    "Number of Trees",
    min_value=50,
    max_value=500,
    value=200,
    step=50
)

selected_lags = st.multiselect(
    "Lag Features",
    [1, 2, 4, 8, 12, 16],
    default=[1, 2, 4, 8]
)

selected_weather_features = st.multiselect(
    "Weather Variables",
    [
        "temperature",
        "precipitation"
    ],
    default=[]
)

# --------------------------------------------------------
# LOAD RESERVOIR DATA
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

# --------------------------------------------------------
# LOAD WEATHER DATA
# --------------------------------------------------------

@st.cache_data
def load_weather(
    latitude,
    longitude
):

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2010-01-01",
        "end_date": "2024-12-31",
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

    return pd.DataFrame(
        {
            "dato_Id": pd.to_datetime(
                data["daily"]["time"]
            ),
            "temperature": data["daily"][
                "temperature_2m_mean"
            ],
            "precipitation": data["daily"][
                "precipitation_sum"
            ]
        }
    )

# --------------------------------------------------------
# FORECAST FUNCTION
# --------------------------------------------------------
def forecast_reservoir(
    reservoir_data,
    weather_data,
    history_length,
    forecast_horizon,
    lags,
    weather_features,
    n_estimators
):

    reservoir_daily = (
        reservoir_data
        .set_index("dato_Id")
        [["fyllingsgrad"]]
        .resample("D")
        .interpolate()
        .reset_index()
    )

    df = pd.merge(
        reservoir_daily,
        weather_data,
        on="dato_Id",
        how="inner"
    )

    df = df.tail(
        history_length
    )

    for lag in lags:

        df[f"lag_{lag}"] = (
            df["fyllingsgrad"]
            .shift(lag)
        )

    df = df.dropna()

    feature_columns = [
        f"lag_{lag}"
        for lag in lags
    ]

    feature_columns.extend(
        weather_features
    )

    train = df.iloc[
        :-forecast_horizon
    ]

    test = df.iloc[
        -forecast_horizon:
    ]

    X_train = train[
        feature_columns
    ]

    y_train = train[
        "fyllingsgrad"
    ]

    X_test = test[
        feature_columns
    ]

    y_test = test[
        "fyllingsgrad"
    ]

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        np.mean(
            (y_test - predictions) ** 2
        )
    )

    return {
        "dates": test["dato_Id"],
        "actual": y_test,
        "predictions": predictions,
        "mae": mae,
        "rmse": rmse
    }

def future_forecast(
    reservoir_data,
    history_length,
    horizon,
    lags,
    n_estimators
):
    """
    Generate future forecasts using recursive prediction
    with seasonal stabilisation.
    """

    reservoir_daily = (
        reservoir_data
        .set_index("dato_Id")
        [["fyllingsgrad"]]
        .resample("D")
        .interpolate()
        .reset_index()
    )

    reservoir_daily = reservoir_daily.tail(
        history_length
    )

    working = reservoir_daily.copy()

    for lag in lags:

        working[f"lag_{lag}"] = (
            working["fyllingsgrad"]
            .shift(lag)
        )

    working = working.dropna()

    feature_columns = [
        f"lag_{lag}"
        for lag in lags
    ]

    X_train = working[
        feature_columns
    ]

    y_train = working[
        "fyllingsgrad"
    ]

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    # ----------------------------------------------------
    # FORECAST
    # ----------------------------------------------------

    forecast_series = list(
        working["fyllingsgrad"]
    )

    future_values = []

    seasonal_window = min(
        365,
        len(forecast_series)
    )

    seasonal_mean = np.mean(
        forecast_series[-seasonal_window:]
    )

    recent_mean = np.mean(
        forecast_series[-30:]
    )

    trend = (
        recent_mean
        -
        np.mean(
            forecast_series[-60:-30]
        )
    )

    for step in range(horizon):

        row = {}

        for lag in lags:

            row[f"lag_{lag}"] = (
                forecast_series[-lag]
            )

        model_prediction = model.predict(
            pd.DataFrame([row])
        )[0]

        trend_component = (
            recent_mean
            +
            trend
            *
            (
                step
                /
                max(horizon, 1)
            )
        )

        seasonal_weight = min(
            step / horizon,
            0.75
        )

        next_prediction = (
            (1 - seasonal_weight)
            * model_prediction
            +
            seasonal_weight
            * seasonal_mean
        )

        next_prediction = (
            0.7
            * next_prediction
            +
            0.3
            * trend_component
        )

        next_prediction = np.clip(
            next_prediction,
            0,
            100
        )

        forecast_series.append(
            next_prediction
        )

        future_values.append(
            next_prediction
        )

    last_date = reservoir_daily[
        "dato_Id"
    ].max()

    future_dates = pd.date_range(
        start=last_date,
        periods=horizon + 1,
        freq="D"
    )[1:]

    return {
        "future_dates": future_dates,
        "future_values": future_values,
        "historical_dates": reservoir_daily[
            "dato_Id"
        ],
        "historical_values": reservoir_daily[
            "fyllingsgrad"
        ]
    }

# --------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------

reservoir_df = load_reservoir_data()

reservoir_df = reservoir_df[
    (reservoir_df["omrType"] == selected_type)
    &
    (reservoir_df["omrnr"] == selected_number)
].copy()

reservoir_df["dato_Id"] = pd.to_datetime(
    reservoir_df["dato_Id"]
)

reservoir_df = reservoir_df.sort_values(
    "dato_Id"
)

if "selected_date" in st.session_state:

    cutoff_date = pd.Timestamp(
        st.session_state.selected_date
    )

    reservoir_df = reservoir_df[
        reservoir_df["dato_Id"]
        <= cutoff_date
    ]

weather_df = load_weather(
    lat,
    lon
)

if "selected_date" in st.session_state:

    weather_df = weather_df[
        weather_df["dato_Id"]
        <= cutoff_date
    ]

# --------------------------------------------------------
# RUN MODEL
# --------------------------------------------------------

if st.button(
    "Generate Forecast"
):

    if len(selected_lags) == 0:

        st.error(
            "Select at least one lag."
        )

    else:

        if forecast_mode == "Model Validation":

            with st.spinner(
                "Training model..."
            ):

                result = forecast_reservoir(
                    reservoir_data=reservoir_df,
                    weather_data=weather_df,
                    history_length=history_length,
                    forecast_horizon=forecast_horizon,
                    lags=selected_lags,
                    weather_features=selected_weather_features,
                    n_estimators=n_estimators
                )

            st.session_state.forecast_result = result
            st.session_state.forecast_mode = (
                "Model Validation"
            )

        elif forecast_mode == "Future Forecast":

            with st.spinner(
                "Generating future forecast..."
            ):

                result = future_forecast(
                    reservoir_data=reservoir_df,
                    history_length=history_length,
                    horizon=forecast_horizon,
                    lags=selected_lags,
                    n_estimators=n_estimators
                )

            st.session_state.forecast_result = result
            st.session_state.forecast_mode = (
                "Future Forecast"
            )

# --------------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------------

if "forecast_result" in st.session_state:

    result = st.session_state.forecast_result

    mode = st.session_state.forecast_mode

    # ------------------------------------------------
    # MODEL VALIDATION
    # ------------------------------------------------

    if mode == "Model Validation":

      
        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "MAE",
                f"{result['mae']:.4f}"
            )

        with col2:

            st.metric(
                "RMSE",
                f"{result['rmse']:.4f}"
            )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=result["dates"],
                y=result["actual"],
                mode="lines",
                name="Actual"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=result["dates"],
                y=result["predictions"],
                mode="lines",
                name="Forecast"
            )
        )

        fig.update_layout(
            title="Reservoir Filling Forecast",
            xaxis_title="Date",
            yaxis_title="Filling Degree (%)",
            template=PLOTLY_TEMPLATE
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.success(
            "Forecast completed successfully."
        )

    # ------------------------------------------------
    # FUTURE FORECAST
    # ------------------------------------------------

    elif mode == "Future Forecast":

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=result["historical_dates"],
                y=result["historical_values"],
                mode="lines",
                name="Historical"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=result["future_dates"],
                y=result["future_values"],
                mode="lines+markers",
                name="Forecast"
            )
        )

        forecast_start = (
            result["historical_dates"]
            .max()
        )

        fig.add_vline(
            x=forecast_start,
            line_dash="dash",
            line_color="red",
            annotation_text="Forecast Start"
        )

        fig.update_layout(
            title="Future Reservoir Forecast",
            xaxis_title="Date",
            yaxis_title="Filling Degree (%)",
            template=PLOTLY_TEMPLATE
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        show_animation = st.checkbox(
            "Show Forecast Animation"
        )

        if (
            show_animation
            and
            "future_values" in result
        ):

            import plotly.graph_objects as go

            frames = []

            for step in range(
                1,
                len(result["future_values"]) + 1
            ):

                frame = go.Frame(
                    data=[
                        go.Scatter(
                            x=result["historical_dates"],
                            y=result["historical_values"],
                            mode="lines",
                            name="Historical",
                            line=dict(
                                color="royalblue"
                            )
                        ),
                        go.Scatter(
                            x=result["future_dates"][:step],
                            y=result["future_values"][:step],
                            mode="lines+markers",
                            name="Forecast",
                            line=dict(
                                color="tomato"
                            )
                        )
                    ],
                    name=str(step)
                )

                frames.append(frame)

            animated_fig = go.Figure(
                data=[
                    go.Scatter(
                        x=result["historical_dates"],
                        y=result["historical_values"],
                        mode="lines",
                        name="Historical",
                        line=dict(
                            color="royalblue"
                        )
                    ),
                    go.Scatter(
                        x=[result["future_dates"][0]],
                        y=[result["future_values"][0]],
                        mode="lines+markers",
                        name="Forecast",
                        line=dict(
                            color="tomato"
                        )
                    )
                ],
                frames=frames
            )

            animated_fig.update_layout(
                title="Animated Reservoir Forecast",
                template=PLOTLY_TEMPLATE,
                xaxis_title="Date",
                yaxis_title="Filling Degree (%)",
                yaxis=dict(
                    range=[0, 1]
                ),
                updatemenus=[
                    {
                        "type": "buttons",
                        "showactive": False,
                        "buttons": [
                            {
                                "label": "▶ Play",
                                "method": "animate",
                                "args": [
                                    None,
                                    {
                                        "frame": {
                                            "duration": 400,
                                            "redraw": True
                                        },
                                        "fromcurrent": True
                                    }
                                ]
                            },
                            {
                                "label": "■ Pause",
                                "method": "animate",
                                "args": [
                                    [None],
                                    {
                                        "frame": {
                                            "duration": 0,
                                            "redraw": False
                                        },
                                        "mode": "immediate"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            )

            st.plotly_chart(
                animated_fig,
                use_container_width=True
            )

        st.success(
            "Future forecast generated."
        )