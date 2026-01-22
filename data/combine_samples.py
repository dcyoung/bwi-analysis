import pandas as pd
import os
import glob

# samples_dir = os.path.join(os.path.dirname(__file__), "mock-samples")
samples_dir = os.path.join(os.path.dirname(__file__), "samples")
out_path = os.path.join(os.path.dirname(__file__), "samples_combined.csv")
SAMPLES_COL_DATASET = "dataset"
SAMPLES_COL_DEVICE_TYPE = "device-type"


def parse_csv(csv_path):
    # Read first two rows for headers
    header_rows = pd.read_csv(csv_path, nrows=2, header=None)
    main_headers = header_rows.iloc[0]
    sub_headers = header_rows.iloc[1]
    # Combine headers
    final_headers = [
        sub if pd.notna(sub) and str(sub).strip() != "" else main
        for main, sub in zip(main_headers, sub_headers)
    ]
    # Read data
    df = pd.read_csv(csv_path, skiprows=2, header=None)
    df.columns = final_headers
    # Add filename column without extension
    df[SAMPLES_COL_DATASET] = os.path.splitext(os.path.basename(csv_path))[0]
    return df


# Parse all files and collect all unique columns
dfs = []
all_columns = set()
for csv_path in glob.glob(os.path.join(samples_dir, "*.csv")):
    df = parse_csv(csv_path)
    dfs.append(df)
    all_columns.update(df.columns)

# Ensure all DataFrames have the same columns (fill missing with NaN)
all_columns = list(all_columns)
for i, df in enumerate(dfs):
    missing = set(all_columns) - set(df.columns)
    for col in missing:
        df[col] = pd.NA
    dfs[i] = df[all_columns]

# Combine all
combined = pd.concat(dfs, ignore_index=True)
combined["Gate / Landmark"] = combined["Gate / Landmark"].map(
    lambda x: "/".join([p.strip() for p in x.strip().split(",")]) if pd.notna(x) else x
)

combined.to_csv(out_path, index=False)
print(f"Combined CSV written to {out_path}")
