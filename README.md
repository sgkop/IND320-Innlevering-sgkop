# IND320 Energy Data Dashboard

## Description

This repository contains the project work completed for IND320.

The project combines data collection, processing, analysis and visualization using:

- NVE Magasinstatistikk API
- Open-Meteo ERA5 weather data
- ENTSO-E cross-border flow data
- Norges Bank API
- Jupyter Notebook
- Streamlit

The objective was to develop an interactive decision-support application for exploring reservoir filling, weather conditions, electricity exchange and forecasting of reservoir filling in Norway.

---

## Main Features

### Data Overview
- Reservoir data exploration
- Interactive data table
- Reservoir plots
- Shared area selection

### Interactive Map
- GeoJSON-based visualization of Norwegian price areas (NO1–NO5)
- Reservoir filling visualization
- Temperature visualization
- Precipitation visualization
- Time-based filtering
- Interactive area selection

### Reservoir Analysis
- STL decomposition
- Spectrogram analysis

### Weather Analysis
- Statistical Process Control (SPC)
- Local Outlier Factor (LOF)

### Correlation Analysis
- Sliding window correlation
- Adjustable lag values
- Adjustable window lengths
- Weather-reservoir relationship analysis

### Forecasting
- Lag-based Machine Learning forecast using Random Forest
- Model Validation
- Future Forecast
- Adjustable lag features
- Adjustable forecast horizon
- Optional weather variables

### Electricity
- Cross-border flow analysis
- ENTSO-E data integration
- Interactive Plotly visualizations

---

## Repository Structure

```text
app.py

pages/
├── 1_Data_Overview.py
├── 2_Interactive_Map.py
├── 3_Reservoir_Analysis.py
├── 4_Weather_Analysis.py
├── 5_Correlation_Analysis.py
├── 6_Forecasting.py
└── 7_Crossborder_Flows.py

data/
└── geojson/

utils/
├── area_coordinates.py
└── theme.py

notebooks/
├── Dashboard basics.ipynb
├── Data quality.ipynb
├── Data sources.ipynb
├── Machine learning.ipynb
└── images/

screencast/
└── IND320 Screencast part4.mp4

requirements.txt
README.md
```

---

## Streamlit Application

https://ind320-innlevering1-sgkop.streamlit.app/

---

## Screencast

The screencast video is included in this repository.

If GitHub does not preview the video directly, select **View Raw** or download the file for playback.

---

## Running the Project Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit application:

```bash
streamlit run app.py
```

---

## Jupyter Notebooks

The notebooks document the development of the project and contain:

- API integration
- Data quality assessment
- Forecasting experiments
- Correlation analysis
- Timezone investigation
- Streamlit planning and documentation

The final notebook also includes project findings, AI usage documentation and a project log.

---

## Bonus Task

The selected bonus task was **Waiting Time**.

Implemented features include:

- `st.cache_data()` for expensive API calls and data processing
- Loading indicators using `st.spinner()`
- Improved responsiveness through caching of frequently used datasets

---

## AI Usage

I acknowledge the use of Microsoft 365 Copilot (https://www.microsoft.com/copilot), based on the GPT-5 chat model, during this project.

Microsoft 365 Copilot was used to discuss project structure, evaluate implementation alternatives, support debugging, explain analytical methods, assist with Streamlit development, review visualisation choices, and improve written documentation.

All code, visualisations, analysis choices and written content were reviewed, tested and adapted before use. Final implementation decisions, interpretations and conclusions remain my own responsibility.
