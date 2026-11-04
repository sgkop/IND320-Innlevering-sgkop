# IND320 Project

## Description

This repository contains the project work completed for IND320.

The project combines data collection, processing, analysis and visualization using:

- NVE Magasinstatistikk API
- Open-Meteo ERA5 weather data
- ENTSO-E cross-border flow data
- Jupyter Notebook
- Streamlit

The project includes:

- Reservoir data exploration
- Cross-border electricity flow analysis
- Statistical Process Control (SPC)
- Local Outlier Factor (LOF)
- STL decomposition
- Spectrogram analysis
- Interactive Streamlit dashboard

---

## Repository Structure

```text
notebooks/
    Dashboard basics.ipynb
    Data quality.ipynb
    Data sources.ipynb

pages/
    1_Data_Table.py
    2_Plots.py
<<<<<<< HEAD
    3_Crossborder_Flows.py
    4_Reservoir_Analysis.py
    5_Weather_Analysis.py
=======
    3_Crossbord_Flows.py
>>>>>>> main

app.py
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

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the Streamlit application:

```bash
streamlit run app.py
```

---

## Jupyter Notebook

The notebooks used for development and documentation are located in:

```text
notebooks/
```
These notebooks contain the exploratory analysis, API integration and analytical methods used in the Streamlit application.

---

## AI Usage

I acknowledge the use of M365 Copilot (https://www.microsoft.com/copilot), based on the GPT-5 chat model, during this project.

M365 Copilot was used to discuss project structure, evaluate implementation alternatives, support debugging, explain analytical methods, assist with Streamlit development, and review written documentation.

All code, visualisations, analysis choices and written content were reviewed, tested and adapted.
