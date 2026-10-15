
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "route_baselines.csv"
OUTPUT_FILE = DATA_DIR / "anomaly_results.csv"

# Provisional threshold for initial testing.
# Tune this using labeled examples or documented evaluation.
ANOMALY_THRESHOLD_PCT = 10.0


def main():
    df = pd.read_csv(INPUT_FILE)

    required = {
        "route", "origin", "destination", "route_type", "week_of",
        "shipment_count", "total_freight_cost_inr", "total_tonne_km",
        "cost_per_tonne_km", "vs_own_history", "vs_similar_routes",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    for col in [
        "cost_per_tonne_km",
        "vs_own_history",
        "vs_similar_routes",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Percentage difference relative to each baseline.
    df["history_difference"] = (
        df["cost_per_tonne_km"] - df["vs_own_history"]
    )
    df["peer_difference"] = (
        df["cost_per_tonne_km"] - df["vs_similar_routes"]
    )

    df["history_difference_pct"] = (
        df["history_difference"] / df["vs_own_history"] * 100
    ).where(df["vs_own_history"] > 0)

    df["peer_difference_pct"] = (
        df["peer_difference"] / df["vs_similar_routes"] * 100
    ).where(df["vs_similar_routes"] > 0)

    threshold = ANOMALY_THRESHOLD_PCT

    df["above_own_history"] = (
        df["history_difference_pct"] >= threshold
    ).fillna(False)

    df["above_similar_routes"] = (
        df["peer_difference_pct"] >= threshold
    ).fillna(False)

    df["flagged"] = (
        df["above_own_history"] | df["above_similar_routes"]
    )

    def explain(row):
        reasons = []

        if row["above_own_history"]:
            reasons.append(
                f"{row['history_difference_pct']:.1f}% above own history"
            )

        if row["above_similar_routes"]:
            reasons.append(
                f"{row['peer_difference_pct']:.1f}% above similar routes"
            )

        if reasons:
            return "; ".join(reasons)

        if pd.isna(row["vs_own_history"]) and pd.isna(
            row["vs_similar_routes"]
        ):
            return "No usable historical or peer baseline"

        return (
            f"No baseline comparison exceeded the "
            f"{threshold:.1f}% threshold"
        )

    df["flag_reason"] = df.apply(explain, axis=1)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("Anomaly detection completed.")
    print(f"Threshold: {threshold:.1f}%")
    print(f"Total records: {len(df)}")
    print(f"Flagged: {int(df['flagged'].sum())}")
    print(f"Not flagged: {int((~df['flagged']).sum())}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
