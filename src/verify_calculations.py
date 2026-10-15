import pandas as pd
from pathlib import Path

DATA = Path("data")

shipments = pd.read_csv(DATA / "shipment_records.csv")
weekly = pd.read_csv(DATA / "weekly_route_costs.csv")

shipments["shipment_date"] = pd.to_datetime(
    shipments["shipment_date"]
)

shipments["week_of"] = (
    shipments["shipment_date"]
    - pd.to_timedelta(
        shipments["shipment_date"].dt.weekday,
        unit="D",
    )
).dt.strftime("%Y-%m-%d")

shipments["tonne_km"] = (
    shipments["quantity_tonnes"] * shipments["distance_km"]
)

keys = ["origin", "destination", "route_type", "week_of"]

expected = (
    shipments.groupby(keys, as_index=False)
    .agg(
        expected_freight=("freight_cost_inr", "sum"),
        expected_tonne_km=("tonne_km", "sum"),
        expected_shipments=("shipment_id", "count"),
    )
)

expected["expected_rate"] = (
    expected["expected_freight"]
    / expected["expected_tonne_km"]
)

weekly["week_of"] = pd.to_datetime(
    weekly["week_of"]
).dt.strftime("%Y-%m-%d")

print("\nStored weekly rate precision:")
print(weekly["cost_per_tonne_km"].head(5).to_list())

comparison = expected.merge(
    weekly,
    on=keys,
    how="outer",
    indicator=True,
    suffixes=("_expected", "_actual"),
)

print("=" * 60)
print("WEEKLY CALCULATION VERIFICATION")
print("=" * 60)

print("Original shipment groups:", len(expected))
print("Weekly output groups:", len(weekly))
print(
    "Matching groups:",
    int((comparison["_merge"] == "both").sum()),
)

if not (comparison["_merge"] == "both").all():
    print("\nFAIL: Some route-week groups are missing or extra.")
    print(
        comparison.loc[
            comparison["_merge"] != "both",
            keys + ["_merge"],
        ].to_string(index=False)
    )
    raise SystemExit(1)

checks = {
    "freight totals": (
        comparison["expected_freight"],
        comparison["total_freight_cost_inr"],
    ),
    "tonne-km totals": (
        comparison["expected_tonne_km"],
        comparison["total_tonne_km"],
    ),
    "shipment counts": (
        comparison["expected_shipments"],
        comparison["shipment_count"],
    ),
}

all_passed = True

for name, (expected_values, actual_values) in checks.items():
    expected_values = pd.to_numeric(
        expected_values, errors="coerce"
    )
    actual_values = pd.to_numeric(
        actual_values, errors="coerce"
    )

    passed = (
        expected_values.notna().all()
        and actual_values.notna().all()
        and (
            expected_values.round(8)
            == actual_values.round(8)
        ).all()
    )

    print(f"{'PASS' if passed else 'FAIL'}: {name}")
    all_passed = all_passed and passed

expected_rates = pd.to_numeric(
    comparison["expected_rate"], errors="coerce"
)

actual_rates = pd.to_numeric(
    comparison["cost_per_tonne_km"], errors="coerce"
)

rate_matches = (
    expected_rates.notna()
    & actual_rates.notna()
    & (
        expected_rates.round(6)
        == actual_rates.round(6)
    )
)

rates_passed = rate_matches.all()

print(f"{'PASS' if rates_passed else 'FAIL'}: weekly rates")
all_passed = all_passed and rates_passed

if not rates_passed:
    comparison["rate_difference"] = (
        actual_rates - expected_rates
    )

    mismatch_columns = keys + [
        "expected_rate",
        "cost_per_tonne_km",
        "rate_difference",
    ]

    print("\nFirst 10 weekly rate mismatches:")

    print(
        comparison.loc[
            ~rate_matches,
            mismatch_columns,
        ]
        .head(10)
        .to_string(index=False)
    )

    print(
        "\nMaximum absolute rate difference:",
        comparison.loc[
            ~rate_matches,
            "rate_difference",
        ].abs().max(),
    )

print("\nSample independently calculated rates:")

print(
    comparison[
        keys
        + [
            "expected_freight",
            "expected_tonne_km",
            "expected_rate",
        ]
    ]
    .head(5)
    .to_string(index=False)
)

print("\n" + "=" * 60)

if not all_passed:
    print("VERIFICATION FAILED: Investigate the mismatches above.")
    raise SystemExit(1)

print("PASS: All weekly calculation checks passed.")
print("=" * 60)