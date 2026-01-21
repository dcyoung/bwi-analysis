import json
import pandas as pd
import os


# Input and output file paths (relative to this script)
script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, "gates.geojson")
output_path = os.path.join(script_dir, "gates.csv")

with open(input_path, "r") as geojson_file:
    data = json.load(geojson_file)

features = data["features"]

rows = []
for feature in features:
    props = feature["properties"]
    coords = feature["geometry"]["coordinates"]
    rows.append(
        {
            "gate": props.get("gate", ""),
            "concourse": props.get("concourse", ""),
            "level": props.get("level", ""),
            "lat": coords[1],
            "lng": coords[0],
        }
    )

df = pd.DataFrame(rows)
df.to_csv(output_path, index=False)
