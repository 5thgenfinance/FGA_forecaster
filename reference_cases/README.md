# Reference cases

Each folder is one workbook scenario: `inputs.json`, `projection_reference.csv`, `summary_reference.json`, `case.json`.
`baseline` is the workbook as delivered (as-of 2026-11-03).

## Add a case
1. Open the workbook in Excel and change the **Main** inputs for the scenario (for example Primary Target Ret Date).
2. Let it recalculate, then save a copy (do not overwrite the baseline workbook).
3. Run, from the project root:
   `python scripts/export_case.py reference/<copy>.xlsx reference_cases/<name> --as-of <today>`
   `--as-of` is the day you recalculated: the workbook uses TODAY() to size the projection.
4. Run `python scripts/compare_to_excel.py` (add `--strict` for the tightest tolerances).

Do not edit `inputs.json` by hand: it is read from the workbook's defined names so it matches the cached values.
