"""Phase 5 - parity harness: cell-by-cell comparison of the Python projection with cached Excel values,
structural invariants, and reference-case discovery.

Tolerances (spec sec. 11): relative 1e-6 and absolute 0.01 for currency columns. Factor/ratio columns use a much
tighter 1e-9 because an absolute 0.01 would hide real errors in a 0-1 quantity.  `strict=True` tightens everything
(abs 1e-6 for currency, 1e-9 relative) - the engine currently meets this on the baseline case.
Excel error cells (#DIV/0!, #N/A, ...) and blanks in the reference are read as NaN and must be NaN in Python.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

COLUMN_GROUPS = {
    "Timeline": ["A", "B", "C", "D"], "Expense inflation": ["E", "F"], "Expenses": ["G", "H"],
    "Survivorship": ["I", "J", "K"], "Lifetime expenses": ["L", "M", "N", "O", "P"],
    "SSI": ["Q", "R", "S", "T", "U", "V", "W", "X", "Y"],
    "Future salary": ["Z", "AA", "AB", "AC", "AD", "AE", "AF", "AG"],
    "Investment income": ["AI", "AJ", "AK"], "Tax": ["AM", "AN", "AO", "AP", "AQ", "AR"],
    "Pre-tax accounts": ["AT", "AU", "AV", "AW", "AX", "AY", "AZ", "BA", "BB"], "Pre-tax distributions": ["BD", "BE"],
    "Post-tax assets": ["BI", "BJ", "BK", "BL", "BM", "BN"], "Mortgage": ["BP", "BQ", "BR", "BS", "BT"],
    "Totals": ["BV", "BW"], "After-tax income": ["BY", "BZ", "CA"], "Surplus & cash flow": ["CC", "CD"],
    "Contributions": ["CF", "CG", "CH"], "Distributions": ["CJ", "CK", "CL", "CM", "CN", "CO", "CQ", "CR"],
    "Dashboard feed": ["CW", "CX", "CY", "CZ", "DA", "DB", "DC", "DD", "DE", "DF", "DG", "DH", "DI", "DJ"],
}
GROUP_OF = {c: g for g, cols in COLUMN_GROUPS.items() for c in cols}
FACTOR_COLUMNS = {"E", "F", "I", "J", "K", "L", "M", "N", "Q", "R", "S", "T", "U", "Z", "AA", "AB", "AG", "AP", "AW", "BA", "BR"}

SUMMARY_KEYS = {  # reference JSON key -> Python summary key
    "C1": "act_assets_C1", "C2": "act_liabilities_C2", "C3": "surplus_C3", "F2": "balance_sheet_assets_F2",
    "F3": "balance_sheet_liabilities_F3", "funding_ratio": "funding_ratio", "peak_assets": "peak_assets",
    "peak_asset_year": "peak_asset_year", "lowest_assets": "lowest_assets",
    "first_positive_cash_flow_year": "first_positive_cash_flow_year",
}
FOCUS_KEYS = {"focus_assets": "total_assets", "focus_cash_flow": "net_cash_flow", "focus_age": "age",
              "focus_expenses": "expenses", "focus_social_security": "social_security",
              "focus_investment_income": "investment_income"}

def _tolerance(col: str, strict: bool) -> tuple[float, float]:
    """(atol, rtol)."""
    if strict:
        return (1e-9, 1e-9) if col in FACTOR_COLUMNS else (1e-6, 1e-9)
    return (1e-9, 1e-9) if col in FACTOR_COLUMNS else (0.01, 1e-6)

def numeric_reference(ref: pd.DataFrame) -> pd.DataFrame:
    """Coerce Excel error strings and blanks to NaN."""
    return ref.apply(pd.to_numeric, errors="coerce")

def compare_frames(df: pd.DataFrame, ref: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
    """One report row per reference column."""
    ref = numeric_reference(ref)
    rows = []
    for col in ref.columns:
        group = GROUP_OF.get(col, "Other")
        if col not in df.columns:
            rows.append(dict(column=col, group=group, rows=0, max_abs_diff=np.nan, max_rel_diff=np.nan,
                             worst_year=None, nan_mismatches=0, status="MISSING"))
            continue
        a, b = df[col].to_numpy(float), ref[col].to_numpy(float)[: len(df)]
        if np.isnan(b).all() and np.isnan(a).all():
            rows.append(dict(column=col, group=group, rows=0, max_abs_diff=0.0, max_rel_diff=0.0, worst_year=None,
                             nan_mismatches=0, status="SKIP"))
            continue
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
        mism = int((np.isnan(a) != np.isnan(b)).sum())
        ok = ~(np.isnan(a) | np.isnan(b))
        diff = np.abs(a - b)
        atol, rtol = _tolerance(col, strict)
        floor = 1e-12 if col in FACTOR_COLUMNS else 1.0      # relative error is meaningless for values near zero
        rel = diff / np.maximum(np.abs(b), floor)
        fail = ok & (diff > atol + rtol * np.abs(b))
        worst = int(np.argmax(np.where(ok, diff, -1))) if ok.any() else None
        year = int(df["B"].iloc[worst]) if worst is not None and "B" in df.columns else None
        rows.append(dict(column=col, group=group, rows=int(ok.sum()),
                         max_abs_diff=float(diff[ok].max()) if ok.any() else 0.0,
                         max_rel_diff=float(rel[ok].max()) if ok.any() else 0.0, worst_year=year,
                         nan_mismatches=mism, status="PASS" if (not fail.any() and mism == 0) else "FAIL"))
    return pd.DataFrame(rows)

def compare_summary(summary: dict, ref: dict, strict: bool = False) -> pd.DataFrame:
    """Compare headline KPIs with the cached workbook values."""
    rows = []
    atol = 1e-4 if strict else 0.01
    def add(name, py, xl):
        if xl is None or isinstance(xl, str):
            rows.append(dict(item=name, python=py, excel=xl, abs_diff=np.nan, status="SKIP")); return
        d = abs(float(py) - float(xl)) if py is not None else np.inf
        tol = 1e-9 if name in ("funding_ratio",) else atol
        rows.append(dict(item=name, python=py, excel=xl, abs_diff=d, status="PASS" if d <= tol + 1e-9 * abs(float(xl)) else "FAIL"))
    for rk, pk in SUMMARY_KEYS.items():
        if rk in ref:
            add(rk, summary.get(pk), ref[rk])
    if "focus" in summary:
        for rk, pk in FOCUS_KEYS.items():
            if rk in ref:
                add(rk, summary["focus"].get(pk), ref[rk])
    return pd.DataFrame(rows)

def check_invariants(df: pd.DataFrame, summary: dict | None = None) -> list[str]:
    """Structural checks that must hold for any valid run. Returns a list of failure messages."""
    bad: list[str] = []
    core = [c for c in df.columns if c not in ("AP", "AR", "D", "AZ") and c not in
            ("CW", "CX", "CY", "CZ", "DA", "DB", "DC", "DD", "DE", "DF", "DG", "DH", "DI", "DJ")]
    vals = df[core].to_numpy(float)
    if not np.isfinite(vals).all():
        bad.append("non-finite values in " + ",".join(c for c in core if not np.isfinite(df[c].to_numpy(float)).all()))
    i = df["I"].to_numpy(float)
    if (i < -1e-12).any() or (i > 1 + 1e-12).any(): bad.append("survivorship outside [0,1]")
    if (np.diff(i) > 1e-12).any(): bad.append("survivorship increases")
    for c in ("J", "L", "S", "Z"):
        v = df[c].to_numpy(float)
        if (v <= 0).any() or (v > 1 + 1e-12).any(): bad.append(f"discount factor {c} outside (0,1]")
    accts = ["AT", "AU", "AY", "BI", "BJ", "BK", "BL", "BM", "BN"]
    if not np.allclose(df["BV"], df[accts].sum(axis=1), rtol=1e-9, atol=1e-6): bad.append("BV != sum of accounts")
    if not np.allclose(df["CA"], df["BY"] - df["BZ"], atol=1e-6): bad.append("CA != BY - BZ")
    if not np.allclose(df["CD"], df["CA"] - df["G"] - df["H"], atol=1e-6): bad.append("CD != CA - G - H")
    for c in ["AU", "AY", "BJ", "BK", "BL", "BM", "BN"]:
        if (df[c] < -1e-6).any(): bad.append(f"negative balance in {c}")
    cd = df["CD"].to_numpy(float)
    if (df["CQ"].to_numpy(float) > np.maximum(-cd, 0) + 1e-6).any(): bad.append("distributions exceed shortfall")
    if ((df["CF"] + df["CG"] + df["CH"]).to_numpy(float) > np.maximum(cd, 0) + 1e-6).any(): bad.append("contributions exceed surplus")
    if "UNFUNDED" in df and not np.allclose(df["UNFUNDED"], np.maximum(-cd - df["CQ"].to_numpy(float), 0), atol=1e-6):
        bad.append("UNFUNDED mismatch")
    if not np.isclose(df["P"].iloc[0], df["O"].sum(), rtol=1e-9): bad.append("P1 != sum(O)")
    if summary is not None:
        if not np.isclose(summary["surplus_C3"], summary["act_assets_C1"] - summary["act_liabilities_C2"], atol=1e-6): bad.append("C3 != C1 - C2")
        if not np.isfinite(summary["funding_ratio"]) or summary["funding_ratio"] < 0: bad.append("funding ratio invalid")
    return bad

@dataclass
class CaseResult:
    name: str
    columns: pd.DataFrame
    summary: pd.DataFrame
    invariants: list
    @property
    def passed(self) -> bool:
        c, s = self.columns, self.summary
        return (not (c["status"] == "FAIL").any() and not (c["status"] == "MISSING").any()
                and not (s["status"] == "FAIL").any() and not self.invariants)

def load_case(folder) -> dict:
    """A case folder holds inputs.json, projection_reference.csv, summary_reference.json and case.json."""
    f = Path(folder)
    meta = json.loads((f / "case.json").read_text())
    return {"name": meta.get("name", f.name), "as_of": date.fromisoformat(meta["as_of_date"]),
            "focus_year": meta.get("focus_year"), "inputs": json.loads((f / "inputs.json").read_text()),
            "ref": pd.read_csv(f / "projection_reference.csv"),
            "summary_ref": json.loads((f / "summary_reference.json").read_text())}

def run_case(folder, tables, ft, strict: bool = False) -> CaseResult:
    from .inputs import ProjectionInputs
    from .pv import run_projection
    case = load_case(folder)
    inputs = ProjectionInputs(**case["inputs"])
    focus = case["focus_year"] or case["summary_ref"].get("focus_year")
    df, summary = run_projection(inputs, tables, ft, case["as_of"], focus_year=focus)
    return CaseResult(case["name"], compare_frames(df, case["ref"], strict),
                      compare_summary(summary, case["summary_ref"], strict), check_invariants(df, summary))

def discover_cases(cases_dir) -> list[Path]:
    d = Path(cases_dir)
    return sorted(p.parent for p in d.glob("*/case.json")) if d.exists() else []

def run_all_cases(cases_dir, tables, ft, strict: bool = False) -> list[CaseResult]:
    return [run_case(p, tables, ft, strict) for p in discover_cases(cases_dir)]

def write_reports(results: list[CaseResult], out_dir) -> list[Path]:
    """Write <case>_columns.csv, <case>_summary.csv and parity_report.md."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    paths, md = [], ["# Parity report", ""]
    for r in results:
        r.columns.to_csv(out / f"{r.name}_columns.csv", index=False); r.summary.to_csv(out / f"{r.name}_summary.csv", index=False)
        paths += [out / f"{r.name}_columns.csv", out / f"{r.name}_summary.csv"]
        md += [f"## {r.name}: {'PASS' if r.passed else 'FAIL'}", "",
               f"- Columns compared: {(r.columns['status'] == 'PASS').sum()} pass, {(r.columns['status'] == 'FAIL').sum()} fail, "
               f"{(r.columns['status'] == 'MISSING').sum()} missing, {(r.columns['status'] == 'SKIP').sum()} skipped",
               f"- Summary items: {(r.summary['status'] == 'PASS').sum()} pass, {(r.summary['status'] == 'FAIL').sum()} fail",
               f"- Invariant failures: {len(r.invariants)}" + (" (" + "; ".join(r.invariants) + ")" if r.invariants else ""), ""]
        g = r.columns[r.columns["status"].isin(["PASS", "FAIL"])].groupby("group").agg(
            columns=("column", "count"), max_abs_diff=("max_abs_diff", "max"), max_rel_diff=("max_rel_diff", "max"))
        md += ["| Group | Columns | Max abs diff | Max rel diff |", "|---|---|---|---|"]
        md += [f"| {k} | {int(v.columns)} | {v.max_abs_diff:.3g} | {v.max_rel_diff:.3g} |" for k, v in g.iterrows()]
        fails = r.columns[r.columns["status"].isin(["FAIL", "MISSING"])]
        if len(fails):
            md += ["", "Failing columns: " + ", ".join(fails["column"])]
        md.append("")
    (out / "parity_report.md").write_text("\n".join(md))
    return paths + [out / "parity_report.md"]
