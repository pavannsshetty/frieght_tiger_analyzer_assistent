
import pandas as pd
from pathlib import Path

# Project folder
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Read weekly route costs
input_file = PROJECT_DIR / "data" / "weekly_route_costs.csv"
df = pd.read_csv(input_file, parse_dates=["week_of"])

# Sort by route and week
route_columns = ["origin", "destination", "route_type"]

df = df.sort_values(
    route_columns + ["week_of"]
).reset_index(drop=True)

# --------------------------------------------------
# BASELINE 1: OWN HISTORY
# --------------------------------------------------

# Create a unique identifier for each route
df["route_id"] = (
    df["origin"] + "|" +
    df["destination"] + "|" +
    df["route_type"]
)

# Create a complete calendar of Mondays so that
# missing shipment weeks are not treated as adjacent weeks.
all_weeks = pd.date_range(
    start=df["week_of"].min(),
    end=df["week_of"].max(),
    freq="W-MON"
)

route_ids = df["route_id"].unique()

calendar = pd.MultiIndex.from_product(
    [route_ids, all_weeks],
    names=["route_id", "week_of"]
).to_frame(index=False)

route_info = df[
    ["route_id", "origin", "destination", "route_type"]
].drop_duplicates("route_id")

calendar = calendar.merge(
    route_info,
    on="route_id",
    how="left"
)

# Add the actual weekly costs to the calendar
calendar = calendar.merge(
    df[
        ["route_id", "week_of", "cost_per_tonne_km"]
    ],
    on=["route_id", "week_of"],
    how="left"
)

calendar = calendar.sort_values(
    ["route_id", "week_of"]
).reset_index(drop=True)

# Calculate the average of the previous 8 calendar weeks.
# shift(1) ensures the current week is excluded.
calendar["vs_own_history"] = (
    calendar.groupby("route_id")["cost_per_tonne_km"]
    .transform(
        lambda s: s.shift(1).rolling(
            window=8,
            min_periods=1
        ).mean()
    )
)

# --------------------------------------------------
# BASELINE 2: SIMILAR ROUTES
# --------------------------------------------------

# Average the weekly rates of all routes sharing
# the same route_type and week_of.
peer_stats = (
    df.groupby(["route_type", "week_of"])
    ["cost_per_tonne_km"]
    .agg(["sum", "count"])
    .reset_index()
)

# Attach the totals and counts to each route.
df = df.merge(
    peer_stats,
    on=["route_type", "week_of"],
    how="left"
)

# Remove this route's own rate and count.
other_route_count = df["count"] - 1
other_route_sum = df["sum"] - df["cost_per_tonne_km"]

df["vs_similar_routes"] = (
    other_route_sum / other_route_count
).where(other_route_count > 0)

df = df.drop(columns=["sum", "count"])

# --------------------------------------------------
# COMBINE BOTH BASELINES
# --------------------------------------------------

df = df.merge(
    calendar[
        ["route_id", "week_of", "vs_own_history"]
    ],
    on=["route_id", "week_of"],
    how="left"
)

# Remove temporary columns
df = df.drop(columns=["route_id"])

# Round values for readability
df["cost_per_tonne_km"] = df["cost_per_tonne_km"].round(6)
df["vs_own_history"] = df["vs_own_history"].round(6)
df["vs_similar_routes"] = df["vs_similar_routes"].round(6)

# Save the results
output_file = PROJECT_DIR / "data" / "route_baselines.csv"

df.to_csv(
    output_file,
    index=False,
    date_format="%Y-%m-%d",
    float_format="%.6f"
)

print("Baseline calculations completed!")
print("Number of weekly route records:", len(df))

print("\nSample results:")
print(
    df[
        [
            "origin",
            "destination",
            "route_type",
            "week_of",
            "cost_per_tonne_km",
            "vs_own_history",
            "vs_similar_routes"
        ]
    ].head(15).to_string(index=False)
)

print("\nSaved file:", output_file)
