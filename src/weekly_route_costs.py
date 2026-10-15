import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

input_file = PROJECT_DIR / "data" / "shipments_with_rates.csv"

df = pd.read_csv(input_file)

df["shipment_date"] = pd.to_datetime(
    df["shipment_date"],
    errors="coerce"
)

df = df.dropna(subset=["shipment_date"])

df["week_of"] = (
    df["shipment_date"].dt.normalize()
    - pd.to_timedelta(df["shipment_date"].dt.weekday, unit="D")
)

df["tonne_km"] = (
    df["quantity_tonnes"] * df["distance_km"]
)

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

weekly["cost_per_tonne_km"] = (
    weekly["total_freight_cost_inr"]
    / weekly["total_tonne_km"]
)

weekly["route"] = (
    weekly["origin"] + " -> " + weekly["destination"]
)

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

weekly = weekly.sort_values(
    ["origin", "destination", "week_of"]
).reset_index(drop=True)

output_file = PROJECT_DIR / "data" / "weekly_route_costs.csv"

weekly.to_csv(
    output_file,
    index=False,
    date_format="%Y-%m-%d",
    float_format="%.6f"
)

print("Weekly route calculations completed!")
print("Number of weekly route records:", len(weekly))

print("\nFirst 10 weekly records:")
print(weekly.head(10).to_string(index=False))

print("\nSaved file:", output_file)