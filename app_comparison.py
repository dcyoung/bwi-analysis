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
    st.subheader("Comparison #1: Wifi vs. Cellular")
    dataset = "D Concourse-Android"
    st.info(dataset)
    st.write(
        "Uses data from the above dataset to compare Cellular vs. Wifi samples. Should be favorable for Wi-Fi across DL, UL, and Latency."
    )

    metric_cols = {
        "Download Speed (Mbps)": (SAMPLES_COL_WIFI_OOKLA_DL, SAMPLES_COL_CELL_OOKLA_DL),
        "Upload Speed (Mbps)": (SAMPLES_COL_WIFI_OOKLA_UL, SAMPLES_COL_CELL_OOKLA_UL),
        "Latency (ms)": (SAMPLES_COL_WIFI_OOKLA_RTT, SAMPLES_COL_CELL_OOKLA_RTT),
    }
    metric = st.selectbox(
        label="Select Metric to Compare",
        options=list(metric_cols.keys()),
        key="comparison1_metric",
    )
    col_wifi, col_cell = metric_cols[metric]

    # Download Speed (Mbps)

    df = samples_df[samples_df[SAMPLES_COL_DATASET] == dataset]
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


def render_comparison_2():
    st.subheader("Comparison 2 - iOS vs. Android")

    datasets = ["B Concourse-Android", "B Concourse-iOS-17"]
    st.info(datasets)
    st.write("Uses data from the above datasets to compare iOS vs. Android.")

    type = st.selectbox(
        label="Select Comparison Type",
        options=["DAS", "Wi-Fi"],
        key="comparison2_type",
    )

    metric_cols = {
        "Wi-Fi": {
            "Download Speed (Mbps)": SAMPLES_COL_WIFI_OOKLA_DL,
            "Upload Speed (Mbps)": SAMPLES_COL_WIFI_OOKLA_UL,
            "Latency (ms)": SAMPLES_COL_WIFI_OOKLA_RTT,
        },
        "DAS": {
            "Download Speed (Mbps)": SAMPLES_COL_CELL_OOKLA_DL,
            "Upload Speed (Mbps)": SAMPLES_COL_CELL_OOKLA_UL,
            "Latency (ms)": SAMPLES_COL_CELL_OOKLA_RTT,
        },
    }

    title = st.selectbox(
        label="Select Metric to Compare",
        options=list(metric_cols[type].keys()),
        key="comparison2_metric",
    )

    metric_col = metric_cols[type][title]
    df = samples_df[samples_df[SAMPLES_COL_DATASET].isin(datasets)][
        [
            SAMPLES_COL_LANDMARK,
            SAMPLES_COL_DEVICE_TYPE,
            metric_col,
        ]
    ]
    # .dropna(subset=[metric_col])

    avg_device_chart = (
        alt.Chart(
            df.groupby(SAMPLES_COL_DEVICE_TYPE, as_index=False)[metric_col].mean()
        )
        .mark_bar()
        .encode(
            y=alt.Y(
                f"{SAMPLES_COL_DEVICE_TYPE}:N",
                title="Device Type",
                sort="-x",
            ),
            x=alt.X(
                f"{metric_col}:Q",
                title=f"Average {title}",
            ),
            tooltip=[
                SAMPLES_COL_DEVICE_TYPE,
                alt.Tooltip(metric_col, title=f"Avg {title}", format=".2f"),
            ],
        )
        .properties(
            title=f"Average {title} by Device Type",
        )
    )

    st.altair_chart(avg_device_chart, width="stretch")

    device_by_landmark_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                f"{SAMPLES_COL_LANDMARK}:N",
                title="Gate / Landmark",
                sort="-y",
            ),
            y=alt.Y(
                f"{metric_col}:Q",
                title=title,
            ),
            color=alt.Color(
                f"{SAMPLES_COL_DEVICE_TYPE}:N",
                title="Device Type",
            ),
            xOffset=f"{SAMPLES_COL_DEVICE_TYPE}:N",
            tooltip=[
                SAMPLES_COL_LANDMARK,
                SAMPLES_COL_DEVICE_TYPE,
                alt.Tooltip(metric_col, title=title, format=".2f"),
            ],
        )
        .properties(
            title=f"{title} by Landmark (iOS vs Android Device Types)",
        )
    )

    st.altair_chart(device_by_landmark_chart, width="stretch")


def render_comparison_3():
    st.subheader("Comparison 3 - iOS 14 w/ and without Pass Point ")
    datasets = ["B Concourse-iOS-14", "B Concourse-iOS-14-PPoff"]
    st.info(datasets)
    st.write(
        "Using data from the above datasets, compare iOS 14 performance with PassPoint enabled vs. disabled. PPoff effectively means disabling wifi offload at network level, forcing all user devices to use DAS (cellular). In this way, we can compare cellular performance metrics BEFORE AND AFTER disabling Wi-Fi PassPoint."
    )
    metric_cols = {
        "Download Speed (Mbps)": SAMPLES_COL_CELL_OOKLA_DL,
        "Upload Speed (Mbps)": SAMPLES_COL_CELL_OOKLA_UL,
        "Latency (ms)": SAMPLES_COL_CELL_OOKLA_RTT,
    }

    title = st.selectbox(
        label="Select Metric to Compare",
        options=list(metric_cols.keys()),
        key="comparison3_metric",
    )

    metric_col = metric_cols[title]
    df = samples_df[samples_df[SAMPLES_COL_DATASET].isin(datasets)][
        [
            SAMPLES_COL_LANDMARK,
            SAMPLES_COL_DATASET,
            metric_col,
        ]
    ]
    # .dropna(subset=[metric_col])

    SAMPLES_COL_CONFIG = "Config"
    df[SAMPLES_COL_CONFIG] = df[SAMPLES_COL_DATASET].map(
        {"B Concourse-iOS-14": "PP On", "B Concourse-iOS-14-PPoff": "PP Off"}
    )

    avg_chart = (
        alt.Chart(df.groupby(SAMPLES_COL_CONFIG, as_index=False)[metric_col].mean())
        .mark_bar()
        .encode(
            y=alt.Y(
                f"{SAMPLES_COL_CONFIG}:N",
                title="Configuration",
                sort="-x",
            ),
            x=alt.X(
                f"{metric_col}:Q",
                title=f"Average {title}",
            ),
            tooltip=[
                SAMPLES_COL_CONFIG,
                alt.Tooltip(metric_col, title=f"Avg {title}", format=".2f"),
            ],
        )
        .properties(
            title=f"Average {title} by Config",
        )
    )

    st.altair_chart(avg_chart, width="stretch")

    by_landmark_chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                f"{SAMPLES_COL_LANDMARK}:N",
                title="Gate / Landmark",
                sort="-y",
            ),
            y=alt.Y(
                f"{metric_col}:Q",
                title=title,
            ),
            color=alt.Color(
                f"{SAMPLES_COL_CONFIG}:N",
                title="Configuration",
            ),
            xOffset=f"{SAMPLES_COL_CONFIG}:N",
            tooltip=[
                SAMPLES_COL_LANDMARK,
                SAMPLES_COL_CONFIG,
                alt.Tooltip(metric_col, title=title, format=".2f"),
            ],
        )
        .properties(
            title=f"{title} by Landmark (PP On vs PP Off)",
        )
    )

    st.altair_chart(by_landmark_chart, width="stretch")


render_comparison_1()
render_comparison_2()
render_comparison_3()
