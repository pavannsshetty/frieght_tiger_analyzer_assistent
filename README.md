# FreightTiger Shipment Cost Anomaly Analyzer

## 1. Project Overview

The FreightTiger Shipment Cost Anomaly Analyzer identifies weekly shipment routes whose freight cost per tonne-kilometre is unusually high compared with historical costs or similar routes.

The system uses Python and pandas to process shipment data, calculate weekly costs, compare baselines, detect potential anomalies, and match relevant context notes to flagged records.

The goal is to make potential cost anomalies easier to identify while keeping the results reproducible and the explanations traceable to available evidence.

## 2. Features

- Shipment data validation and cost calculation.
- Weekly aggregation by route and route type.
- Historical baseline comparison using previous calendar weeks.
- Comparison with other routes of the same route type.
- Configurable percentage threshold for anomaly detection.
- Context-note matching with route and date restrictions.
- CSV output validation.
- Automated unit tests and reproducibility checks.

## 3. Technology Stack

- Python
- pandas
- pytest
- CSV for input and output data

No LLM or external AI API is used in the current implementation. The detection and note-matching rules are deterministic.

## 4. Project Structure

```text
freight-tiger-analyzer/
├── data/
│   ├── shipment_records.csv
│   ├── context_notes.csv
│   ├── sample_output_format_v2.csv
│   ├── shipments_with_rates.csv
│   ├── weekly_route_costs.csv
│   ├── route_baselines.csv
│   ├── anomaly_results.csv
│   └── note_matching_results.csv
├── src/
│   ├── calculate_rates.py
│   ├── weekly_route_costs.py
│   ├── calculate_baselines.py
│   ├── detect_anomalies.py
│   ├── match_notes.py
│   ├── validate_output.py
│   ├── check_reproducibility.py
│   ├── verify_calculations.py
│   └── verify_baselines.py
├── tests/
│   ├── test_anomaly_rules.py
│   └── test_anomaly_verification.py
├── docs/
│   ├── reproducibility.md
│   └── token_cost_report.md
├── .gitignore
├── README.md
└── requirements.txt
```

## 5. Setup

Install Python, then open a terminal in the project directory.

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install pandas pytest
```

Place the supplied input CSV files inside the `data/` directory.

## 6. How to Run

Execute the scripts in this order:

```bash
python src/calculate_rates.py
python src/weekly_route_costs.py
python src/calculate_baselines.py
python src/detect_anomalies.py
python src/match_notes.py
python src/validate_output.py
```

Run the unit tests:

```bash
pytest -q
```

Run the three-run reproducibility check:

```bash
python src/check_reproducibility.py
```

The final output is saved to:

`data/note_matching_results.csv`

## 7. Cost Calculation

The cost per tonne-kilometre is calculated as:

Cost per tonne-km = Total freight cost / Total tonne-kilometres

For each shipment:

Tonne-kilometres = Quantity in tonnes × Distance in kilometres

Weekly route cost is calculated using the sum of freight costs divided by the sum of tonne-kilometres for that route and week. This avoids taking an unweighted average of individual shipment rates.

## 8. Baseline Comparison

### Historical baseline

The historical baseline uses the previous eight calendar weeks and excludes the current week. When fewer prior weeks are available, the available history is used without padding or extrapolation.

### Similar-route baseline

The peer baseline compares a route with other routes of the same route type during the same week. The route itself is excluded from the peer average.

## 9. Anomaly Detection

The current implementation uses a provisional threshold of 10%.

A weekly route record is flagged when its cost is at least 10% above either its historical baseline or its similar-route baseline.

Records without a usable baseline cannot trigger a flag from that comparison.

The threshold is an initial engineering choice and has not yet been established as optimal through a labeled evaluation dataset. Being above a baseline is a signal for review, not proof of fraud or an incorrect invoice.

## Anomaly Detection Threshold

The current implementation uses a provisional 10% threshold to flag weekly route costs that exceed either the route's historical baseline or the average for similar routes.

A record is flagged when at least one valid baseline comparison is 10% or higher. The threshold is an implementation choice for this submission, not a confirmed requirement from the challenge specification.

The percentage difference is calculated as:

`((Current Rate - Baseline Rate) / Baseline Rate) * 100`

Records without a usable baseline are not automatically flagged by that comparison.

## 10. Context-Note Matching

The system checks whether an available context note matches the route and relevant time period.

- N001: Chennai–Bangalore flooding during the documented period.
- N002: Ahmedabad–Mumbai festival surcharge during the week beginning January 20, 2025.
- N003: Nationwide diesel-price increase, matched conservatively to the week beginning May 5, 2025 when the observed historical increase is approximately 5–7%.

Notes that describe normal conditions, unaffected routes, or no meaningful rate impact are not used to justify an increase.

A matched note provides contextual support, not definitive proof of causation. Unmatched flagged records remain unexplained.

## 11. Output Format

The final CSV uses these columns in the required order:

1. `route`
2. `week_of`
3. `cost_per_tonne_km`
4. `vs_own_history`
5. `vs_similar_routes`
6. `flagged`
7. `matched_note_id`
8. `reason`

Verdict meanings:

- `Yes`: flagged, with no matched supporting note.
- `No (justified)`: flagged, with a matched context note.
- `No`: not flagged by the current baseline comparison.

## 12. Validation and Reproducibility

The current implementation has completed the following checks:

- Output contains 728 weekly route records.
- Output column names and order match the required schema.
- Required output fields and verdict values pass structural validation.
- Every justified verdict has a note ID.
- Unexplained flags have no matched note ID.
- Five unit tests passed.
- Three consecutive pipeline runs produced identical output files.

The current final run reported:

- 90 flagged records.
- 87 unexplained flags.
- 3 note-supported flags.
- 638 records not flagged.

These are results from the current implementation and should not be interpreted as an independently verified anomaly rate.

## 13. LLM Usage and Cost

The current pipeline uses no LLM calls, external model APIs, or model-generated explanations.

- LLM calls: 0
- LLM input tokens: 0
- LLM output tokens: 0
- LLM API cost: ₹0

These figures cover LLM usage only, not electricity, local compute, development time, or other possible operating costs.

## 14. Limitations and Future Improvements

- Evaluate the 10% threshold using labeled examples.
- Add end-to-end tests using known normal and anomalous records.
- Review context-note matches against the original notes.
- Measure precision and recall when labeled data becomes available.
- Improve handling of missing baselines and sparse route histories.
- Add a user-facing interface for reviewing anomalies and asking questions about results.

## 15. Conclusion

The project provides a deterministic, reproducible baseline for weekly freight-cost anomaly analysis. It combines historical comparisons, peer comparisons, conservative context-note matching, and automated validation to make potential cost increases easier to review.