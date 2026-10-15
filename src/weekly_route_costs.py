
import pandas as pd
from pathlib import Path

# Locate the project folder
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Read the shipment data with calculated rates
input_file = PROJECT_DIR / "data" / "shipments_with_rates.csv"

df = pd.read_csv(input_file)

# Convert shipment_date to a proper date
df["shipment_date"] = pd.to_datetime(
    df["shipment_date"],
    errors="coerce"
)

# Remove rows with invalid dates
df = df.dropna(subset=["shipment_date"])

# Find the Monday of each shipment's week
df["week_of"] = (
    df["shipment_date"].dt.normalize()
    - pd.to_timedelta(df["shipment_date"].dt.weekday, unit="D")
)

# Calculate tonne-kilometres for each shipment
df["tonne_km"] = (
    df["quantity_tonnes"] * df["distance_km"]
)

# Group shipments by route, route type, and week
group_columns = [
    "origin",
    "destination",
    "route_type",
    "week_of"
]

weekly = (
    df.groupby(group_columns, as_index=False)
    .agg(
        shipment_count=("shipment_id", "count"),
        total_freight_cost_inr=("freight_cost_inr", "sum"),
        total_tonne_km=("tonne_km", "sum")
    )
)

# Calculate the correct weekly cost per tonne per km
weekly["cost_per_tonne_km"] = (
    weekly["total_freight_cost_inr"]
    / weekly["total_tonne_km"]
)

# Create a readable route name
weekly["route"] = (
    weekly["origin"] + " -> " + weekly["destination"]
)

# Arrange columns for easier reading
weekly = weekly[
    [
        "route",
        "origin",
        "destination",
        "route_type",
        "week_of",
        "shipment_count",
        "total_freight_cost_inr",
        "total_tonne_km",
        "cost_per_tonne_km"
    ]
]

# Sort the results by route and week
weekly = weekly.sort_values(
    ["origin", "destination", "week_of"]
).reset_index(drop=True)

# Save weekly results
output_file = PROJECT_DIR / "data" / "weekly_route_costs.csv"

weekly.to_csv(
    output_file,
    index=False,
    date_format="%Y-%m-%d",
    float_format="%.6f"
)

# Display results
print("Weekly route calculations completed!")
print("Number of weekly route records:", len(weekly))

print("\nFirst 10 weekly records:")
print(weekly.head(10).to_string(index=False))

print("\nSaved file:", output_file)
