
import re
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

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

# Notes must describe a plausible upward cost impact.
POSITIVE_COST_TERMS = (
    "higher trip costs",
    "higher costs",
    "costs rose",
    "costs rising",
    "pushing up",
    "increase in cost",
    "increased costs",
    "surcharge",
    "higher freight costs",
    "cost increase",
)

# These phrases indicate that the note does not support
# an increase in costs for the route and period.
NEGATIVE_IMPACT_TERMS = (
    "not significantly affected",
    "no significant disruptions",
    "no major disruptions",
    "without rate change",
    "costs absorbed without",
    "not part of dataset",
    "no rate change",
    "returned to normal",
    "roads were passable again",
)


def normalize_text(value):
    """Normalize text for deterministic matching."""
    text = str(value).lower().strip()
    text = text.replace("→", "->")
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_route(value):
    """Convert route names to a consistent representation."""
    text = normalize_text(value)
    text = text.replace(" -> ", "-")
    text = text.replace("->", "-")
    text = text.replace(" ", "")
    return text


def note_applies_to_route(route, applies_to):
    """Check exact route applicability or an all-routes note."""
    route = normalize_route(route)
    applies_to = normalize_route(applies_to)

    return (
        applies_to == "allroutes"
        or route == applies_to
    )


def note_supports_cost_increase(note_text):
    """
    Return True only when the note contains a recognized
    positive cost-impact phrase and no negative-impact phrase.
    """
    text = normalize_text(note_text)

    if any(term in text for term in NEGATIVE_IMPACT_TERMS):
        return False

    return any(
        term in text for term in POSITIVE_COST_TERMS
    )


def note_matches_time(note_id, note_date, week):
    """
    Check whether a note is applicable to the weekly record.

    General rule:
    The note date must fall during the current week or
    the preceding seven days.

    N003 exception:
    The supplied note describes a diesel-price increase
    starting the week of 2025-05-05. It does not explicitly
    establish the duration of the effect, so only that
    specific week is supported.
    """
    days_since_note = (week - note_date).days

    if days_since_note < 0 or days_since_note > 7:
        return False

    # Conservative time restriction for the nationwide
    # diesel-price note N003.
    if note_id == "N003":
        return week == pd.Timestamp("2025-05-05")

    return True


def retrieve_supporting_note(row, notes):
    """
    Retrieve a note using route applicability, date and content.

    The function is deterministic: the most recent matching
    note is selected, with note ID used to break ties.
    """
    week = pd.to_datetime(
        row["week_of"], errors="coerce"
    )

    if pd.isna(week):
        return "", ""

    week = week.normalize()
    route = row["route"]
    candidates = []

    for _, note in notes.iterrows():
        note_id = str(note["note_id"]).strip()

        note_date = pd.to_datetime(
            note["date"], errors="coerce"
        )

        if pd.isna(note_date):
            continue

        note_date = note_date.normalize()

        # Verify the note applies to this route.
        if not note_applies_to_route(
            route, note["applies_to"]
        ):
            continue

        # Verify the note applies to this time period.
        if not note_matches_time(
            note_id, note_date, week
        ):
            continue

        note_text = str(note["note"])

        # Verify that the note supports an upward cost impact.
        if not note_supports_cost_increase(note_text):
            continue

        candidates.append(
            (note_date, note_id, note_text)
        )

    if not candidates:
        return "", ""

    # Most recent note first; note ID breaks date ties.
    candidates.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )

    _, note_id, note_text = candidates[0]

    return note_id, note_text


def main():
    # Load input files.
    results = pd.read_csv(INPUT_FILE)
    notes = pd.read_csv(NOTES_FILE)

    # Validate anomaly-result columns.
    required_result_cols = {
        "route",
        "week_of",
        "cost_per_tonne_km",
        "vs_own_history",
        "vs_similar_routes",
        "flagged",
    }

    missing = required_result_cols - set(results.columns)

    if missing:
        raise ValueError(
            "Missing anomaly result columns: "
            f"{sorted(missing)}"
        )

    # Validate context-note columns.
    required_note_cols = {
        "note_id",
        "date",
        "applies_to",
        "note",
    }

    missing = required_note_cols - set(notes.columns)

    if missing:
        raise ValueError(
            "Missing context note columns: "
            f"{sorted(missing)}"
        )

    results["week_of"] = pd.to_datetime(
        results["week_of"], errors="coerce"
    )

    output_rows = []

    for _, row in results.iterrows():
        flagged_value = str(
            row["flagged"]
        ).strip().lower()

        is_flagged = flagged_value in {
            "true", "1", "yes"
        }

        note_id = ""
        reason = ""

        if not is_flagged:
            # No anomaly was detected by the baseline rules.
            verdict = "No"
            reason = (
                "Not flagged by the current baseline "
                "comparison."
            )

        else:
            # Search for a supporting context note.
            note_id, note_text = retrieve_supporting_note(
                row, notes
            )

            if note_id:
                # The anomaly has a relevant supporting note.
                verdict = "No (justified)"

                # Preserve the note's original wording.
                reason = (
                    f"Context note {note_id} provides "
                    f"supporting cost-related context: "
                    f"{note_text} [Note ID: {note_id}]"
                )

            else:
                # The anomaly remains unexplained by the notes.
                verdict = "Yes"
                reason = (
                    "Flagged by the baseline comparison, "
                    "but no supporting route- and time-matched "
                    "cost note was found. The cause remains "
                    "unexplained."
                )

        output_rows.append({
            "route": row["route"],
            "week_of": (
                row["week_of"].strftime("%Y-%m-%d")
                if pd.notna(row["week_of"])
                else ""
            ),
            "cost_per_tonne_km": (
                row["cost_per_tonne_km"]
            ),
            "vs_own_history": row["vs_own_history"],
            "vs_similar_routes": row["vs_similar_routes"],
            "flagged": verdict,
            "matched_note_id": note_id,
            "reason": reason,
        })

    # Preserve the exact required output column order.
    output = pd.DataFrame(
        output_rows,
        columns=OUTPUT_COLUMNS,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print("Context-note retrieval completed.")
    print(f"Total records: {len(output)}")
    print(
        "Justified flags:",
        int(
            (output["flagged"] == "No (justified)").sum()
        ),
    )
    print(
        "Unexplained flags:",
        int((output["flagged"] == "Yes").sum()),
    )
    print(
        "Not flagged:",
        int((output["flagged"] == "No").sum()),
    )
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
