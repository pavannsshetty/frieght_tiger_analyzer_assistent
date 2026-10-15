
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "anomaly_results.csv"
NOTES_FILE = DATA_DIR / "context_notes.csv"
OUTPUT_FILE = DATA_DIR / "note_matching_results.csv"

OUTPUT_COLUMNS = [
    "route",
    "week_of",
    "cost_per_tonne_km",
    "vs_own_history",
    "vs_similar_routes",
    "flagged",
    "matched_note_id",
    "reason",
]


def normalize_route(value):
    return (
        str(value)
        .lower()
        .replace(" ", "")
        .replace("→", "-")
        .replace("->", "-")
    )


def match_note(row, notes):
    week = pd.to_datetime(row["week_of"], errors="coerce")
    if pd.isna(week):
        return "", "No supporting context note matched."

    route = normalize_route(row["route"])
    history_pct = pd.to_numeric(
        row["history_difference_pct"], errors="coerce"
    )

    for _, note in notes.iterrows():
        note_id = str(note["note_id"]).strip()
        note_date = pd.to_datetime(note["date"], errors="coerce")
        applies_to = str(note["applies_to"]).strip().lower()

        # N001: Chennai-Bangalore flooding, Feb 24–Mar 8, 2025.
        if note_id == "N001":
            if (
                route == "chennai-bangalore"
                and pd.Timestamp("2025-02-24")
                <= week
                <= pd.Timestamp("2025-03-03")
            ):
                return note_id, (
                    "Flooding disrupted Chennai-Bangalore truck movement "
                    "from Feb 24 to Mar 8, forcing detours and higher trip "
                    "costs (context note N001)."
                )

        # N002: Ahmedabad-Mumbai festival surcharge week.
        elif note_id == "N002":
            if (
                route == "ahmedabad-mumbai"
                and week == pd.Timestamp("2025-01-20")
            ):
                return note_id, (
                    "A temporary festival-week transporter surcharge was "
                    "reported for Ahmedabad-Mumbai (context note N002)."
                )

        # N003: nationwide diesel-price increase.
        # Require the observed own-history increase to be around 5–7%.
        elif note_id == "N003":
            if (
                applies_to == "all routes"
                and week == pd.Timestamp("2025-05-05")
                and pd.notna(history_pct)
                and 5.0 <= history_pct <= 7.0
            ):
                return note_id, (
                    "A nationwide diesel-price increase was reported from "
                    "the week of May 5, with transportation costs rising "
                    "roughly 5–7%. The observed own-history increase is "
                    f"{history_pct:.1f}% (context note N003)."
                )

    return "", "No route- and time-matched note sufficiently explains this cost increase."


def main():
    results = pd.read_csv(INPUT_FILE)
    notes = pd.read_csv(NOTES_FILE)

    required_result_cols = {
        "route",
        "week_of",
        "cost_per_tonne_km",
        "vs_own_history",
        "vs_similar_routes",
        "history_difference_pct",
        "flagged",
    }
    missing = required_result_cols - set(results.columns)
    if missing:
        raise ValueError(f"Missing anomaly result columns: {sorted(missing)}")

    required_note_cols = {"note_id", "date", "applies_to", "note"}
    missing = required_note_cols - set(notes.columns)
    if missing:
        raise ValueError(f"Missing context note columns: {sorted(missing)}")

    results["week_of"] = pd.to_datetime(
        results["week_of"], errors="coerce"
    )

    output_rows = []

    for _, row in results.iterrows():
        is_flagged = str(row["flagged"]).strip().lower() in {
            "true", "1", "yes"
        }

        if not is_flagged:
            verdict = "No"
            note_id = ""
            reason = "Not flagged by the current baseline comparison."
        else:
            note_id, note_reason = match_note(row, notes)

            if note_id:
                verdict = "No (justified)"
                reason = note_reason
            else:
                verdict = "Yes"
                reason = (
                    "Flagged by the current baseline comparison, but "
                    "no supporting context note was matched. "
                    + note_reason
                )

        output_rows.append({
            "route": row["route"],
            "week_of": (
                row["week_of"].strftime("%Y-%m-%d")
                if pd.notna(row["week_of"]) else ""
            ),
            "cost_per_tonne_km": row["cost_per_tonne_km"],
            "vs_own_history": row["vs_own_history"],
            "vs_similar_routes": row["vs_similar_routes"],
            "flagged": verdict,
            "matched_note_id": note_id,
            "reason": reason,
        })

    output = pd.DataFrame(output_rows, columns=OUTPUT_COLUMNS)
    output.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("Context-note matching completed.")
    print(f"Total records: {len(output)}")
    print(
        "Justified flags:",
        (output["flagged"] == "No (justified)").sum()
    )
    print(
        "Unexplained flags:",
        (output["flagged"] == "Yes").sum()
    )
    print(
        "Not flagged:",
        (output["flagged"] == "No").sum()
    )
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
