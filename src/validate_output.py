
import csv
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent

output_file = PROJECT_DIR / "data" / "note_matching_results.csv"
template_file = PROJECT_DIR / "data" / "sample_output_format_v2.csv"

# Required columns from the supplied template header
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

# Read the template header only.
# The example rows in the supplied template contain unquoted commas,
# so reading the whole template with pandas may fail.
with open(template_file, "r", newline="", encoding="utf-8-sig") as f:
    template_header = next(csv.reader(f))

print("Checking output format...\n")

# Check 1: Template header
if template_header == required_columns:
    print("PASS: Required template columns are correct.")
else:
    print("FAIL: Template header differs from the expected columns.")
    print("Found:", template_header)

# Check 2: Generated output
df = pd.read_csv(output_file, dtype=str, keep_default_na=False)

if df.columns.tolist() == required_columns:
    print("PASS: Output has the correct columns and order.")
else:
    print("FAIL: Output columns or order are incorrect.")
    print("Found:", df.columns.tolist())

# Check 3: Required fields
if len(df) > 0:
    print("PASS: Output contains", len(df), "records.")
else:
    print("FAIL: Output is empty.")

# Check 4: Required fields should not be blank
for column in ["route", "week_of", "cost_per_tonne_km", "flagged", "reason"]:
    blank_count = int((df[column].str.strip() == "").sum())

    if blank_count == 0:
        print(f"PASS: {column} has no blank values.")
    else:
        print(f"FAIL: {column} has {blank_count} blank values.")

# Check 5: Verdicts and note IDs
allowed_verdicts = {"Yes", "No", "No (justified)"}
invalid_verdicts = sorted(set(df["flagged"]) - allowed_verdicts)

if not invalid_verdicts:
    print("PASS: Verdict values are valid.")
else:
    print("FAIL: Unexpected verdicts:", invalid_verdicts)

# A justified verdict must have a note ID.
justified = df["flagged"] == "No (justified)"
missing_note_ids = int((justified & (df["matched_note_id"].str.strip() == "")).sum())

if missing_note_ids == 0:
    print("PASS: Every justified row has a matched note ID.")
else:
    print("FAIL:", missing_note_ids, "justified rows have no note ID.")

# Unexplained rows should not claim a supporting note.
unexplained = df["flagged"] == "Yes"
incorrect_note_ids = int(
    (unexplained & (df["matched_note_id"].str.strip() != "")).sum()
)

if incorrect_note_ids == 0:
    print("PASS: Unexplained rows have blank note IDs.")
else:
    print("FAIL:", incorrect_note_ids, "unexplained rows have note IDs.")

print("\nValidation checks completed.")
