import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import os

SAMPLES_COL_DATASET = "dataset"
SAMPLES_COL_DEVICE_TYPE = "Device/OS"
SAMPLES_COL_LANDMARK = "Gate / Landmark"
SAMPLES_COL_WIFI_OOKLA_UL = "Wi-Fi Ookla UL"
SAMPLES_COL_CELL_OOKLA_UL = "Cellular Ookla UL"
SAMPLES_COL_WIFI_OOKLA_DL = "Wi-Fi Ookla DL"
SAMPLES_COL_CELL_OOKLA_DL = "Cellular Ookla DL"
SAMPLES_COL_WIFI_OOKLA_RTT = "Wi-Fi Ookla RTT"
SAMPLES_COL_CELL_OOKLA_RTT = "Cellular Ookla RTT"
GATES_COL_GATE = "gate"
GATES_COL_LAT = "lat"
GATES_COL_LNG = "lng"

# Always use this as the airport center
bwi_airport_center = [39.179459, -76.668473]

# Paths
data_dir = os.path.join(os.path.dirname(__file__), "data")
gates_path = os.path.join(data_dir, "gates.csv")
samples_path = os.path.join(
    data_dir,
    "2026_01_21_samples_combined.csv",
    # "samples_combined_jittered.csv"
)

gates_df = pd.read_csv(gates_path)
samples_df = pd.read_csv(samples_path)

st.set_page_config(layout="wide")

st.title("BWI Analysis App")


def render_comparison_1():
    st.subheader("Wifi vs. Cellular Comparison #1:")
    st.write(
        "Compare DAS to Helium in Concourse D Android data. Should be favorable. DL, UL, and Latency."
    )

    metric_cols = {
        "Download Speed (Mbps)": (SAMPLES_COL_WIFI_OOKLA_DL, SAMPLES_COL_CELL_OOKLA_DL),
        "Upload Speed (Mbps)": (SAMPLES_COL_WIFI_OOKLA_UL, SAMPLES_COL_CELL_OOKLA_UL),
        "Latency (ms)": (SAMPLES_COL_WIFI_OOKLA_RTT, SAMPLES_COL_CELL_OOKLA_RTT),
    }
    metric = st.selectbox(
        label="Select Metric to Compare",
        options=list(metric_cols.keys()),
    )
    col_wifi, col_cell = metric_cols[metric]

    # Download Speed (Mbps)

    df = samples_df[samples_df[SAMPLES_COL_DATASET] == "D Concourse-Android"]
    # Combined grouped bar chart: Wi-Fi and Cellular Download Speeds by Landmark
    dl_melted = df.melt(
        id_vars=[SAMPLES_COL_LANDMARK],
        value_vars=[col_wifi, col_cell],
        var_name="Network",
        value_name=metric,
    )
    dl_melted["Network"] = dl_melted["Network"].map(
        {col_wifi: "Wi-Fi", col_cell: "Cellular"}
    )

    # Chart: Average Download Speed by Network Type (Wi-Fi vs Cellular, all landmarks)
    avg_dl_chart = (
        alt.Chart(dl_melted.groupby("Network", as_index=False)[metric].mean())
        .mark_bar()
        .encode(
            y=alt.Y("Network:N", title="Network Type"),
            x=alt.X(f"{metric}:Q", title=f"Average {metric}"),
            color=alt.Color(
                "Network:N",
                scale=alt.Scale(
                    domain=["Wi-Fi", "Cellular"], range=["#1f77b4", "#ff7f0e"]
                ),
                legend=None,
            ),
            tooltip=["Network", metric],
        )
        .properties(
            title=f"Avg {metric} per Landmark",
        )
    )
    st.altair_chart(avg_dl_chart, width="stretch")

    dl_chart = (
        alt.Chart(dl_melted)
        .mark_bar()
        .encode(
            x=alt.X(f"{SAMPLES_COL_LANDMARK}:N", title="Gate / Landmark", sort="-y"),
            y=alt.Y(f"{metric}:Q", title=metric),
            color=alt.Color(
                "Network:N",
                scale=alt.Scale(
                    domain=["Wi-Fi", "Cellular"], range=["#1f77b4", "#ff7f0e"]
                ),
            ),
            xOffset="Network:N",
            tooltip=[SAMPLES_COL_LANDMARK, "Network", metric],
        )
        .properties(
            # width=600, height=400,
            title=f"Wi-Fi vs Cellular {metric} by Landmark"
        )
    )
    st.altair_chart(dl_chart, width="stretch")


render_comparison_1()
