import csv
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent

output_file = PROJECT_DIR / "data" / "note_matching_results.csv"
template_file = PROJECT_DIR / "data" / "sample_output_format_v2.csv"

required_columns = [
    "route",
    "week_of",
    "cost_per_tonne_km",
    "vs_own_history",
    "vs_similar_routes",
    "flagged",
    "matched_note_id",
    "reason"
]

with open(template_file, "r", newline="", encoding="utf-8-sig") as f:
    template_header = next(csv.reader(f))

print("Checking output format...\n")

if template_header == required_columns:
    print("PASS: Required template columns are correct.")
else:
    print("FAIL: Template header differs from the expected columns.")
    print("Found:", template_header)

df = pd.read_csv(output_file, dtype=str, keep_default_na=False)

if df.columns.tolist() == required_columns:
    print("PASS: Output has the correct columns and order.")
else:
    print("FAIL: Output columns or order are incorrect.")
    print("Found:", df.columns.tolist())

if len(df) > 0:
    print("PASS: Output contains", len(df), "records.")
else:
    print("FAIL: Output is empty.")

for column in ["route", "week_of", "cost_per_tonne_km", "flagged", "reason"]:
    blank_count = int((df[column].str.strip() == "").sum())

    if blank_count == 0:
        print(f"PASS: {column} has no blank values.")
    else:
        print(f"FAIL: {column} has {blank_count} blank values.")

allowed_verdicts = {"Yes", "No", "No (justified)"}
invalid_verdicts = sorted(set(df["flagged"]) - allowed_verdicts)

if not invalid_verdicts:
    print("PASS: Verdict values are valid.")
else:
    print("FAIL: Unexpected verdicts:", invalid_verdicts)

justified = df["flagged"] == "No (justified)"
missing_note_ids = int((justified & (df["matched_note_id"].str.strip() == "")).sum())

if missing_note_ids == 0:
    print("PASS: Every justified row has a matched note ID.")
else:
    print("FAIL:", missing_note_ids, "justified rows have no note ID.")

unexplained = df["flagged"] == "Yes"
incorrect_note_ids = int(
    (unexplained & (df["matched_note_id"].str.strip() != "")).sum()
)

if incorrect_note_ids == 0:
    print("PASS: Unexplained rows have blank note IDs.")
else:
    print("FAIL:", incorrect_note_ids, "unexplained rows have note IDs.")

print("\nValidation checks completed.")