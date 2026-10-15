# Reproducibility Report

## Test Summary

The shipment cost anomaly detection pipeline was executed three consecutive times using the same input data and configuration.

- Total weekly route records: 728
- Anomalies detected: 90
- Justified anomalies: 2
- Unexplained anomalies: 88
- Records not flagged: 638
- Automated tests: 15 passed

## Output Consistency

All three executions produced the same SHA-256 hash:

`d631e7287a21d97b81471a410ed2c508d775c5f64b96998bc1022a30b02a73cc`

This confirms that the generated output file was identical across the three tested executions.

## Validation

The output validator confirmed the required column names and order, all 728 records, valid verdict values, and correct note-ID handling for justified and unexplained anomalies.

## Limitations

This test demonstrates repeatability for the current inputs and environment. It does not independently prove that the anomaly thresholds or context-note matches are factually correct.