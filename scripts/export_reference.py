"""Export cached workbook reference values used by the parity tests.
Usage: python scripts/export_reference.py reference/FGA_Client_Onboarding_Calculator.xlsx data
Writes data/projection_reference.csv (Projection rows 7-70, Excel column codes; error cells kept as text)
and data/summary_reference.json (Projection C1:C3, F2:F3 and Retirement Dashboard KPIs)."""
import sys, json
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter as gl

def main(xlsx, out):
    wb = load_workbook(xlsx, data_only=True)
    p, d = wb["Projection"], wb["Retirement Dashboard"]
    rows = [[p.cell(r, c).value for c in range(1, p.max_column + 1)] for r in range(7, 71)]
    pd.DataFrame(rows, columns=[gl(c) for c in range(1, p.max_column + 1)]).dropna(axis=1, how="all") \
        .to_csv(f"{out}/projection_reference.csv", index=False)
    summary = {
        "C1": p["C1"].value, "C2": p["C2"].value, "C3": p["C3"].value, "F2": p["F2"].value, "F3": p["F3"].value,
        "funding_ratio": d["A6"].value, "focus_year": d["M3"].value,
        "focus_assets": d["I6"].value, "focus_cash_flow": d["M6"].value,
        "first_positive_cash_flow_year": d["E30"].value, "peak_assets": d["E31"].value,
        "peak_asset_year": d["E32"].value, "lowest_assets": d["E33"].value,
        "focus_age": d["M30"].value, "focus_expenses": d["M31"].value,
        "focus_social_security": d["M32"].value, "focus_investment_income": d["M33"].value,
    }
    json.dump(summary, open(f"{out}/summary_reference.json", "w"), indent=1)
    print("wrote projection_reference.csv and summary_reference.json")

if __name__ == "__main__":
    main(*sys.argv[1:3])
