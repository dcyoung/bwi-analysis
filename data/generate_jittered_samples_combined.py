from pathlib import Path
import pandas as pd
import numpy as np


# Paths
DATA_DIR = Path(__file__).parent
INPUT_PATH = DATA_DIR / "samples_combined.csv"
OUTPUT_PATH = DATA_DIR / "samples_combined_jittered.csv"

# Metric columns to jitter
METRIC_COLS = [
    "RSRP",
    "RSRQ",
    "Cellular Ookla DL",
    "Cellular Ookla UL",
    "Cellular Ookla RTT",
    "RSSI",
    "Wi-Fi Ookla DL",
    "Wi-Fi Ookla UL",
    "Wi-Fi Ookla RTT",
]

DEVICE_TYPES = ["android", "ios"]
DATASET_CHOICES = [f"mock-dataset-{i}" for i in range(1, 6)]

# Read gates for randomization
gates_path = DATA_DIR / "gates.csv"
gates_df = pd.read_csv(gates_path)
gate_choices = gates_df["gate"].dropna().unique().tolist()

# Read main data
df = pd.read_csv(INPUT_PATH)

# Number of duplicates (including original)
N_DATASETS = 5

dfs = []
for i in range(N_DATASETS):
    df_copy = pd.concat([df.copy(), df.copy(), df.copy()])
    # Jitter metric columns
    for col in METRIC_COLS:
        if col in df_copy.columns:
            if "RSRP" in col or "RSRQ" in col or "RSSI" in col:
                df_copy[col] = df_copy[col] + np.random.randint(
                    -3, 4, size=len(df_copy)
                )
            else:
                df_copy[col] = df_copy[col] + np.random.randint(
                    -10, 11, size=len(df_copy)
                )
    # Randomize Device Type
    df_copy["Device/OS"] = np.random.choice(DEVICE_TYPES, size=len(df_copy))
    # Randomize dataset col
    df_copy["dataset"] = np.random.choice(DATASET_CHOICES, size=len(df_copy))
    # Randomize Gate / Landmark
    if "Gate / Landmark" in df_copy.columns:
        df_copy["Gate / Landmark"] = np.random.choice(gate_choices, size=len(df_copy))
    dfs.append(df_copy)

# Concatenate all
result = pd.concat(dfs, ignore_index=True)

# Write to new CSV
result.to_csv(OUTPUT_PATH, index=False)
print(f"Jittered combined dataset written to {OUTPUT_PATH}")
