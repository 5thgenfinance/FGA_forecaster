"""Read model inputs from the Excel workbook (defined names) and export reference cases.

A reference case = inputs.json + the workbook's cached Projection values for those inputs + KPI JSON.
Workflow to add a case: change the Main inputs in Excel, recalculate, save, then run
    python scripts/export_case.py <workbook.xlsx> reference_cases/<name> --as-of YYYY-MM-DD
(`--as-of` must be the date the workbook was recalculated, because TODAY() sets the projection length).
"""
from __future__ import annotations
import json
from datetime import date, datetime
from pathlib import Path
import pandas as pd

SPECIAL_CELLS = {"sleeve3_deployed": ("Main", "B55")}     # no defined name in the workbook
DATE_FIELDS = {"p_dob", "s_dob", "t_ret_date", "t_s_ret_date"}
OPTIONAL_DATE_FIELDS = {"s_dob", "t_s_ret_date"}
STRING_FIELDS = {"retired", "p_gender", "mort_table", "inc_tax_status", "InflationScenario", "COLAScenario",
                 "t_expenses", "t_salary", "t_income", "t_sup_salary", "t_sup_income", "t_SSI_PIA", "t_cashcush"}
BOOL_FIELDS = {"disabled"}

def _cell_value(wb, name):
    dn = wb.defined_names.get(name)
    if dn is None:
        return None, False
    sheet, coord = next(iter(dn.destinations))
    return wb[sheet][coord.replace("$", "")].value, True

def read_inputs(xlsx) -> dict:
    """Return a dict accepted by ProjectionInputs(**d)."""
    from openpyxl import load_workbook
    from .inputs import ProjectionInputs
    wb = load_workbook(xlsx, data_only=True)
    out = {}
    for field in ProjectionInputs.model_fields:
        if field in SPECIAL_CELLS:
            sheet, coord = SPECIAL_CELLS[field]; v, found = wb[sheet][coord].value, True
        else:
            v, found = _cell_value(wb, field)
        if not found:
            continue
        if field in DATE_FIELDS:
            if v in (None, ""):
                if field in OPTIONAL_DATE_FIELDS: out[field] = None
                continue
            out[field] = v.date() if isinstance(v, datetime) else v
        elif field in STRING_FIELDS:
            if v not in (None, ""): out[field] = str(v)
        elif field in BOOL_FIELDS:
            out[field] = bool(v)
        else:
            out[field] = 0 if v in (None, "") else v
    return ProjectionInputs(**out).model_dump(mode="json")

def export_case(xlsx, folder, as_of: date, name: str | None = None, focus_year: int | None = None) -> Path:
    """Write a reference-case folder from a recalculated workbook."""
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter as gl
    f = Path(folder); f.mkdir(parents=True, exist_ok=True)
    inputs = read_inputs(xlsx)
    wb = load_workbook(xlsx, data_only=True)
    p, d = wb["Projection"], wb["Retirement Dashboard"]
    rows = [[p.cell(r, c).value for c in range(1, p.max_column + 1)] for r in range(7, 71)]
    pd.DataFrame(rows, columns=[gl(c) for c in range(1, p.max_column + 1)]).dropna(axis=1, how="all") \
        .to_csv(f / "projection_reference.csv", index=False)
    summary = {"C1": p["C1"].value, "C2": p["C2"].value, "C3": p["C3"].value, "F2": p["F2"].value, "F3": p["F3"].value,
               "funding_ratio": d["A6"].value, "focus_year": d["M3"].value, "focus_assets": d["I6"].value,
               "focus_cash_flow": d["M6"].value, "first_positive_cash_flow_year": d["E30"].value,
               "peak_assets": d["E31"].value, "peak_asset_year": d["E32"].value, "lowest_assets": d["E33"].value,
               "focus_age": d["M30"].value, "focus_expenses": d["M31"].value,
               "focus_social_security": d["M32"].value, "focus_investment_income": d["M33"].value}
    (f / "summary_reference.json").write_text(json.dumps(summary, indent=1, default=str))
    (f / "inputs.json").write_text(json.dumps(inputs, indent=1))
    (f / "case.json").write_text(json.dumps({"name": name or f.name, "as_of_date": as_of.isoformat(),
                                             "focus_year": focus_year or summary["focus_year"],
                                             "workbook": Path(xlsx).name}, indent=1))
    return f
