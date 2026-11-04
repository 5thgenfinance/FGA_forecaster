# FGA_forecaster - Phase 0 + Phase 1

Python refactor of the RMIF Excel retirement model.

## Setup
1. Create a venv and run `pip install -r requirements.txt`.
2. Put `FGA_Client_Onboarding_Calculator.xlsx` in `reference/` (git-ignored).
3. Re-export tables (optional; CSVs are included):
   `python scripts/export_workbook.py reference/FGA_Client_Onboarding_Calculator.xlsx data`
   (then re-export `data/projection_reference.csv` if the workbook changes)
4. Run `pytest` from the project root. Expect all tests to pass.

## Layout
- `model/` config, inputs, helpers, tax, mortality, curves (pluggable discount curves), scenarios (pluggable inflation)
- `data/` exported tables and cached Projection reference values (rows 7-70)
- `tests/` Phase 0 shape tests; Phase 1 helper and column-parity tests

Note: survivorship uses ASOFDATE() (retirement date when PRERET). Blank qx raises unless allow_blank=True.
Proprietary - all rights reserved.
