import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import os

SAMPLES_COL_DATASET = "dataset"
SAMPLES_COL_DEVICE_TYPE = "Device/OS"
SAMPLES_COL_LANDMARK = "Gate / Landmark"
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

# Read data
gates_df = pd.read_csv(gates_path)
samples_df = pd.read_csv(samples_path)
dataset_options = sorted(samples_df[SAMPLES_COL_DATASET].dropna().unique().tolist())


def get_metric_description(field_name: str) -> str:
    name = field_name.lower()
    if "ookla dl" in name:
        return "**Ookla (Speedtest) DL = Download speed.** Measures download throughput, typically reported in Mbps. Higher DL values are better."
    if "ookla rtt" in name:
        return (
            "**Ookla (Speedtest) RTT = Round-Trip Time.** Measures latency as the time (usually in milliseconds) it takes for a packet to go from the device → server → device.\n\n"
            "Lower RTT = more responsive connection\n\n"
            "**Typical values**\n"
            "- Excellent: ~5–20 ms\n"
            "- Good: 20–50 ms\n"
            "- Poor: 100+ ms"
        )
    if "ookla ul" in name:
        return "**Ookla (Speedtest) UL = Upload speed.** Measures upload throughput, typically reported in Mbps. Higher UL values are better."
    if "rssi" in name:
        return "**RSSI = Received Signal Strength Indicator.** Measures the strength/quality of the wireless signal. Usually measured in dBm. Higher values are better."
    if "rsrq" in name:
        return (
            "**RSRQ = Reference Signal Received Quality.**\n"
            "Measures the quality of a cellular signal, not just its strength. Higher values are better."
        )
    return ""


st.set_page_config(layout="wide")

st.title("BWI Analysis App")

num_comparisons = st.select_slider("Comparisons", options=[1, 2, 3], value=1)

FILTER_COLS = st.columns(num_comparisons)

filtered_dfs = []
for i, col in enumerate(FILTER_COLS):
    with col:
        st.subheader("Filter Samples")

        # --- UI: Filter by filename ---
        selected_datasets = st.multiselect(
            "Include data from:",
            dataset_options[:],
            default=dataset_options[:],
            key=f"dataset_select_{i}",
        )
        # Subset DataFrame
        filtered_df = samples_df[
            samples_df[SAMPLES_COL_DATASET].isin(selected_datasets)
        ]
        device_type_options = sorted(
            filtered_df[SAMPLES_COL_DEVICE_TYPE].dropna().unique().tolist()
        )

        selected_device_types = st.multiselect(
            "Include device types:",
            device_type_options[:],
            default=device_type_options[:],
            key=f"device_type_select_{i}",
        )

        # Subset DataFrame again based on selected device types
        filtered_df = filtered_df[
            filtered_df[SAMPLES_COL_DEVICE_TYPE].isin(selected_device_types)
        ]

        with st.expander("See included samples"):
            st.dataframe(filtered_df, width="stretch")

        filtered_dfs.append(filtered_df)

stats_cols = st.columns(num_comparisons)
for col, filtered_df in zip(stats_cols, filtered_dfs):
    with col:
        if filtered_df.empty:
            st.warning("No data available for the selected filters.")
            continue

        with st.expander("See Filtered Summary Stats"):
            st.dataframe(filtered_df.describe(), width="stretch")


selected_metric_cols = []
metric_viz_headers = st.columns(num_comparisons)
for i, (col, filtered_df) in enumerate(zip(metric_viz_headers, filtered_dfs)):
    if filtered_df.empty:
        continue
    with col:
        st.subheader("Metric Visualization")
        metric_cols = sorted(
            [
                c
                for c in filtered_df.columns
                if any(key in str(c) for key in ["Ookla", "RSSI", "RSRP", "RSRQ"])
            ]
        )

        metric_col = st.selectbox(
            "Select a metric to visualize:", metric_cols, key=f"metric_select_{i}"
        )

        # Show description for selected metric
        desc = get_metric_description(metric_col)

        st.markdown(desc or "No description available for this metric.")

        selected_metric_cols.append(metric_col)


plot_cols = st.columns(num_comparisons)
for col, metric_col, filtered_df in zip(plot_cols, selected_metric_cols, filtered_dfs):
    if filtered_df.empty:
        continue
    with col:
        # --- Group by location and average selected metric ---
        grouped = (
            filtered_df.groupby(SAMPLES_COL_LANDMARK)[metric_col].mean().reset_index()
        )
        st.subheader(f"Average {metric_col} per Landmark")
        bar_chart = (
            alt.Chart(grouped)
            .mark_bar()
            .encode(
                x=alt.X(f"{SAMPLES_COL_LANDMARK}:N", title="Landmark"),
                y=alt.Y(f"{metric_col}:Q", title=f"Avg {metric_col}"),
            )
            .properties(width=400, height=350)
        )
        st.altair_chart(bar_chart, width="stretch")

        st.subheader("Histogram of Average per Landmark")
        values = grouped[metric_col].dropna().values
        if len(values) > 0:
            # Use Altair's binning and count() style
            hist_chart = (
                alt.Chart(grouped)
                .mark_bar()
                .encode(
                    x=alt.X(f"{metric_col}", bin=True, title=f"Avg {metric_col}"),
                    y=alt.Y("count()", title="Count of Landmarks"),
                )
                .properties(width=400, height=350)
            )
            st.altair_chart(hist_chart, width="stretch")
        else:
            st.info("No data to display histogram.")

for col, metric_col, filtered_df in zip(plot_cols, selected_metric_cols, filtered_dfs):
    if filtered_df.empty:
        continue
    with col:
        grouped = (
            filtered_df.groupby(SAMPLES_COL_LANDMARK)[metric_col].mean().reset_index()
        )
        st.subheader(f"Average {metric_col} per Landmark")
        # Join grouped averages to gates.csv lat/lng

        grouped[SAMPLES_COL_LANDMARK] = (
            grouped[SAMPLES_COL_LANDMARK].astype(str).str.strip()
        )
        gates_df[GATES_COL_GATE] = gates_df[GATES_COL_GATE].astype(str).str.strip()
        merged = pd.merge(
            grouped,
            gates_df,
            left_on=SAMPLES_COL_LANDMARK,
            right_on=GATES_COL_GATE,
            how="left",
        )
        if GATES_COL_LAT in merged.columns and GATES_COL_LNG in merged.columns:
            map_df = merged.dropna(subset=[GATES_COL_LAT, GATES_COL_LNG, metric_col])
            map_df[GATES_COL_LAT] = pd.to_numeric(
                map_df[GATES_COL_LAT], errors="coerce"
            )
            map_df[GATES_COL_LNG] = pd.to_numeric(
                map_df[GATES_COL_LNG], errors="coerce"
            )
            # Scale radius and color based on metric value
            if not map_df.empty:
                min_val = map_df[metric_col].min()
                max_val = map_df[metric_col].max()
                # Avoid division by zero
                if max_val - min_val == 0:
                    map_df["scaled_radius"] = 100
                    map_df["color"] = [[255, 140, 0, 160]] * len(map_df)
                else:
                    map_df["scaled_radius"] = 2 + 15 * (
                        map_df[metric_col] - min_val
                    ) / (max_val - min_val)

                    # Color: interpolate from light yellow to orange
                    def color_fn(val):
                        frac = (val - min_val) / (max_val - min_val)
                        r = int(255)
                        g = int(200 - 60 * frac)
                        b = int(0)
                        a = int(80 + 80 * frac)
                        return [r, g, b, a]

                    map_df["color"] = map_df[metric_col].apply(color_fn)

            n_missing = grouped.shape[0] - map_df.shape[0]
            if n_missing > 0:
                st.info(
                    f"{n_missing} sampled landmark(s) missing lat/lng or metric data and are excluded from the map."
                )
            # Add a color legend for the map
            st.markdown("**Legend:**")
            min_val = float(min_val)
            max_val = float(max_val)
            legend_html = f"""
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 0.9em;">{min_val:.2f}</span>
                    <div style="background: linear-gradient(90deg, rgb(255,200,0), rgb(255,140,0)); width: 120px; height: 16px; border-radius: 4px; border: 1px solid #ccc;"></div>
                    <span style="font-size: 0.9em;">{max_val:.2f}</span>
                    <span style="font-size: 0.9em; margin-left: 8px;">{metric_col}</span>
                </div>
                """
            st.markdown(legend_html, unsafe_allow_html=True)
            st.pydeck_chart(
                pdk.Deck(
                    map_style="light",
                    initial_view_state=pdk.ViewState(
                        latitude=bwi_airport_center[0],
                        longitude=bwi_airport_center[1],
                        zoom=15,
                        pitch=0,
                    ),
                    layers=[
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=map_df,
                            get_position=f"[{GATES_COL_LNG}, {GATES_COL_LAT}]",
                            get_radius="scaled_radius",
                            radius_min_pixels=10,
                            radius_max_pixels=500,
                            get_fill_color="color",
                            pickable=True,
                            auto_highlight=True,
                            get_line_color=[0, 0, 0],
                            line_width_min_pixels=1,
                        ),
                    ],
                    tooltip={"text": f"{{{SAMPLES_COL_LANDMARK}}}: {{{metric_col}}}"},
                )
            )
        else:
            st.info("No lat/lng columns found in gates.csv for mapping.")
