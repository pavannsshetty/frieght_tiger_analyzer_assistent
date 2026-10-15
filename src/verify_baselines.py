
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

weekly = pd.read_csv(
    DATA_DIR / "weekly_route_costs.csv",
    parse_dates=["week_of"],
)

baselines = pd.read_csv(
    DATA_DIR / "route_baselines.csv",
    parse_dates=["week_of"],
)

keys = ["origin", "destination", "route_type", "week_of"]

comparison = weekly[keys].merge(
    baselines[keys],
    on=keys,
    how="outer",
    indicator=True,
)

if not (comparison["_merge"] == "both").all():
    print("FAIL: Weekly and baseline route-week records differ.")
    print(comparison["_merge"].value_counts())
    raise SystemExit(1)

print("PASS: All route-week records match.")


route_columns = ["origin", "destination", "route_type"]

weekly = weekly.sort_values(
    route_columns + ["week_of"]
).copy()

weekly["route_id"] = (
    weekly["origin"] + "|" +
    weekly["destination"] + "|" +
    weekly["route_type"]
)

all_weeks = pd.date_range(
    weekly["week_of"].min(),
    weekly["week_of"].max(),
    freq="W-MON",
)

route_info = weekly[
    ["route_id"] + route_columns
].drop_duplicates()

calendar = pd.MultiIndex.from_product(
    [route_info["route_id"], all_weeks],
    names=["route_id", "week_of"],
).to_frame(index=False)

calendar = calendar.merge(
    route_info,
    on="route_id",
    how="left",
)

calendar = calendar.merge(
    weekly[["route_id", "week_of", "cost_per_tonne_km"]],
    on=["route_id", "week_of"],
    how="left",
)

calendar = calendar.sort_values(
    ["route_id", "week_of"]
)

calendar["expected_history"] = (
    calendar.groupby("route_id")["cost_per_tonne_km"]
    .transform(
        lambda s: s.shift(1).rolling(
            window=8,
            min_periods=1,
        ).mean()
    )
)

expected_history = calendar.dropna(
    subset=["cost_per_tonne_km"]
)[
    ["route_id", "week_of", "expected_history"]
]

actual_history = baselines.copy()
actual_history["route_id"] = (
    actual_history["origin"] + "|" +
    actual_history["destination"] + "|" +
    actual_history["route_type"]
)

history_check = expected_history.merge(
    actual_history[
        ["route_id", "week_of", "vs_own_history"]
    ],
    on=["route_id", "week_of"],
    how="left",
)

history_ok = (
    history_check["expected_history"].round(6)
    == history_check["vs_own_history"].round(6)
) | (
    history_check["expected_history"].isna()
    & history_check["vs_own_history"].isna()
)

print(
    f"{'PASS' if history_ok.all() else 'FAIL'}: "
    "historical baselines"
)

if not history_ok.all():
    print("\nFirst historical mismatches:")
    print(
        history_check.loc[
            ~history_ok
        ].head(10).to_string(index=False)
    )

peer_groups = weekly.groupby(
    ["route_type", "week_of"]
)

weekly["expected_peers"] = peer_groups[
    "cost_per_tonne_km"
].transform("sum") - weekly["cost_per_tonne_km"]

weekly["peer_count"] = peer_groups[
    "cost_per_tonne_km"
].transform("count") - 1

weekly["expected_peers"] = (
    weekly["expected_peers"] / weekly["peer_count"]
).where(weekly["peer_count"] > 0)

peer_check = weekly.merge(
    baselines[
        keys + ["vs_similar_routes"]
    ],
    on=keys,
    how="left",
)

peer_ok = (
    peer_check["expected_peers"].round(6)
    == peer_check["vs_similar_routes"].round(6)
) | (
    peer_check["expected_peers"].isna()
    & peer_check["vs_similar_routes"].isna()
)

print(
    f"{'PASS' if peer_ok.all() else 'FAIL'}: "
    "similar-route baselines"
)

if not peer_ok.all():
    print("\nFirst peer baseline mismatches:")
    print(
        peer_check.loc[
            ~peer_ok,
            keys + [
                "expected_peers",
                "vs_similar_routes",
            ],
        ].head(10).to_string(index=False)
    )

if not history_ok.all() or not peer_ok.all():
    raise SystemExit(1)

print("\nPASS: All baseline verification checks passed.")
