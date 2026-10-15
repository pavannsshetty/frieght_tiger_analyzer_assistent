
import pandas as pd
from pathlib import Path

# Find the project folder
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Read the shipment CSV
input_file = PROJECT_DIR / "data" / "shipment_records.csv"

df = pd.read_csv(input_file)

print("Shipment data loaded successfully!")
print("Total shipments:", len(df))
print("Columns:", df.columns.tolist())

# Convert required columns to numeric values
numeric_columns = [
    "quantity_tonnes",
    "distance_km",
    "freight_cost_inr"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Check for missing or invalid values
valid_rows = (
    df[numeric_columns].notna().all(axis=1)
    & (df["quantity_tonnes"] > 0)
    & (df["distance_km"] > 0)
    & (df["freight_cost_inr"] >= 0)
)

invalid_count = int((~valid_rows).sum())

# Calculate cost per tonne per kilometre
df["cost_per_tonne_km"] = float("nan")

df.loc[valid_rows, "cost_per_tonne_km"] = (
    df.loc[valid_rows, "freight_cost_inr"]
    / (
        df.loc[valid_rows, "quantity_tonnes"]
        * df.loc[valid_rows, "distance_km"]
    )
)

# Display the first five results
print("\nFirst 5 shipment rates:")

print(
    df[
        [
            "shipment_id",
            "origin",
            "destination",
            "quantity_tonnes",
            "distance_km",
            "freight_cost_inr",
            "cost_per_tonne_km"
        ]
    ].head().to_string(index=False)
)

print("\nValid shipments:", int(valid_rows.sum()))
print("Invalid shipments:", invalid_count)

# Save results without modifying the original CSV
output_file = PROJECT_DIR / "data" / "shipments_with_rates.csv"

df.to_csv(output_file, index=False, float_format="%.6f")

print("\nCalculated data saved to:", output_file)
