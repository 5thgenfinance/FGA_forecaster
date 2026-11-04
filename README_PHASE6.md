# Phase 6 - client visualizations

## Install
    pip install -r requirements.txt
    pip install -r requirements-optional.txt     # kaleido (PNG/PDF) and streamlit (UI) - both optional

If PNG export fails with a Chrome error, run `plotly_get_chrome` once, or skip `--png/--pdf` (the HTML report always works).

## Run
    python -m app.cli run --inputs inputs.example.json --as-of 2026-11-03 --out results --client-name "Pat and Chris" --scenarios --pdf
    streamlit run app/ui.py

Outputs in `results/`: projection.csv, projection.xlsx, summary.json, report.html, and with --png/--pdf charts/*.png and report.pdf.
Exit codes: 0 ok, 2 invalid inputs (field names listed), 3 file/data problem, 4 PNG/PDF unavailable (other files written).
Use `--offline` to embed Plotly in the HTML (3 MB) when the client's device has no internet.

## Branding
Copy `brand.example.json`, edit colors, firm name, title and `extra_disclosure`, and pass `--brand yourfile.json`.
Unknown keys are rejected. All text is HTML-escaped.

## Charts
1. Resources vs. lifetime spending need (spec chart: Year/CW vs DH and DF)
2. Net cash flow by year (spec chart: Year/CW vs CX)
3. Funding ratio gauge   4. Savings by account type   5. Income by source, tax and spending
6. Funding bridge (C1, C2, C3)   7. What-if comparison (with --scenarios)

Charts stop when the primary client reaches age 100 (`chart_age_limit`); all KPIs use the full projection.
"Total resources" = account balances + present value of Social Security + present value of future earnings (Excel DH).

## Before client use
- The disclosure text in `model/report.py` is a draft. Have your compliance reviewer approve it, and the hypothetical-
  performance language, before any client sees the output.
- The return assumptions in the sample (12.5% long-term, 14% Sleeve 3 income) are the workbook's. Review them.
- `summary.json` carries `adviser_notes`: known model behaviors to review (see DECISIONS.md).
- `samples/` was generated from the default sample household, not a real client.
