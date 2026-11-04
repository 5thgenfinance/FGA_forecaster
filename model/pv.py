"""Phase 4 - backward (present-value) columns, dashboard feed, summary KPIs and the top-level run_projection().

Backward columns: AJ, AK, AQ, AR, CC, CR.  Dashboard feed: CW..DJ (Excel fills only the first 52 rows,
so rows 53-64 are NaN by default; pass feed_years=None for the full horizon).
Summary: Projection!C1:C3 (PV-based surplus), F2:F3 (balance sheet), funding ratio, dashboard KPIs.

Excel quirks reproduced for parity (spec issue #3, #8):
  * AK year 1 = SUM(AJ) with no divisor; AK year t>=2 = SUM(AJ[t:]) / K[t-1], returns 0 when U[t-1] = 0.
  * AR year 1 = SUM(AQ); year t>=2 divides by the prior-row mid-year survivorship T[t-1].
  * C1 = X1 + AK1 + BW1, where BW1 = BV1 x J1 (end-of-year-1 assets discounted one year at the hurdle rate).
  * C3 (PV-based) and CC (yearly, includes salary asset, excludes account balances) are different by design.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import numpy as np
import pandas as pd
from .engine import ModelTables
from .inputs import ProjectionInputs
from .loop import ForwardTables, opening_balances, run_through_phase3

DASHBOARD_FEED_YEARS = 52     # Projection!CW7:DJ58
BACKWARD_COLUMNS = ["AJ", "AK", "AQ", "AR", "CC", "CR"]
FEED_COLUMNS = ["CW", "CX", "CY", "CZ", "DA", "DB", "DC", "DD", "DE", "DF", "DG", "DH", "DI", "DJ"]

def _suffix(x: np.ndarray) -> np.ndarray:
    return np.cumsum(x[::-1])[::-1]

def run_backward(inputs: ProjectionInputs, df: pd.DataFrame, feed_years: int | None = DASHBOARD_FEED_YEARS) -> pd.DataFrame:
    """Compute AJ, AK, AQ, AR, CC, CR and the dashboard feed CW:DJ from a Phase A+B DataFrame."""
    n = len(df)
    c = {k: df[k].to_numpy(float) for k in df.columns}
    ob = opening_balances(inputs)
    AJ = c["AI"] * c["S"] * c["T"]
    sj = _suffix(AJ)
    AK = np.zeros(n)
    AK[0] = sj[0]
    for t in range(1, n):
        AK[t] = 0.0 if c["U"][t - 1] == 0 else sj[t] / c["K"][t - 1]
    AQ = c["AO"] * c["N"]
    sq = _suffix(AQ)
    AR = np.zeros(n)
    AR[0] = sq[0]
    for t in range(1, n):
        AR[t] = np.nan if c["T"][t - 1] == 0 else sq[t] / c["T"][t - 1]   # Excel shows #DIV/0! here
    CC = AK + c["X"] + c["AF"] - c["P"]
    CR = c["CQ"] * c["L"]

    prev_pre = np.concatenate([[ob["AU"] + ob["AY"]], (c["AU"] + c["AY"])[:-1]])
    prev_post = np.concatenate([[ob["BJ"] + ob["BK"] + ob["BL"] + ob["BM"] + ob["BI"]],
                                (c["BJ"] + c["BK"] + c["BL"] + c["BM"] + c["BI"])[:-1]])
    prev_real = np.concatenate([[ob["BN"]], c["BN"][:-1]])
    CY, DA, CZ = c["X"], c["AF"], AK
    DH = CY + DA + prev_pre + prev_post + prev_real
    feed = {"CW": c["B"], "CX": c["CD"], "CY": CY, "CZ": CZ, "DA": DA, "DB": prev_pre, "DC": prev_post,
            "DD": prev_real, "DE": c["BT"], "DF": c["P"], "DG": c["BT"] + c["P"], "DH": DH,
            "DI": c["BS"] + c["O"], "DJ": c["AE"] + AJ - AQ + CR}
    out = pd.DataFrame({"AJ": AJ, "AK": AK, "AQ": AQ, "AR": AR, "CC": CC, "CR": CR, **feed})
    if feed_years is not None and feed_years < n:
        out.loc[feed_years:, FEED_COLUMNS] = np.nan
    return out

def build_summary(inputs: ProjectionInputs, df: pd.DataFrame) -> dict:
    """Projection!C1:C3, F2:F3, funding ratio and dashboard milestones."""
    ob = opening_balances(inputs)
    c1 = float(df["X"].iloc[0] + df["AK"].iloc[0] + df["BW"].iloc[0])
    c2 = float(df["P"].iloc[0])
    f2 = float(sum(ob.values()))
    mortgage_balance = float(inputs.mortgage)
    f3 = float(df["AQ"].sum() + mortgage_balance)
    feed = df.dropna(subset=["DH"])
    peak_i = int(feed["DH"].to_numpy().argmax())
    pos = df[(df["CX"] > 0) & (df["CW"] >= inputs.t_ret_date.year)]
    return {"act_assets_C1": c1, "act_liabilities_C2": c2, "surplus_C3": c1 - c2,
            "funding_ratio": c1 / c2 if c2 else float("nan"),
            "balance_sheet_assets_F2": f2, "balance_sheet_liabilities_F3": f3,
            "projection_years": int(len(df)), "feed_years": int(len(feed)),
            "peak_assets": float(feed["DH"].iloc[peak_i]), "peak_asset_year": int(feed["CW"].iloc[peak_i]),
            "lowest_assets": float(feed.loc[feed["CW"] > 0, "DH"].min()),
            "first_positive_cash_flow_year": int(pos["CW"].iloc[0]) if len(pos) else None}

def dashboard_metrics(df: pd.DataFrame, focus_year: int) -> dict:
    """Focus-year KPIs (Retirement Dashboard I6, M6, M30:M33).  Excel only searches the first 34 rows
    for the detail block; here any projected year is allowed, and a missing year raises."""
    row = df[df["B"] == focus_year]
    if row.empty:
        raise ValueError(f"focus year {focus_year} outside projection {int(df['B'].min())}-{int(df['B'].max())}")
    r = row.iloc[0]
    if pd.isna(r["DH"]):
        raise ValueError(f"focus year {focus_year} is beyond the dashboard feed ({int(df['DH'].notna().sum())} years)")
    return {"focus_year": int(focus_year), "total_assets": float(r["DH"]), "net_cash_flow": float(r["CX"]),
            "age": int(r["C"]), "expenses": float(r["G"] + r["H"]), "social_security": float(r["V"]),
            "investment_income": float(r["AI"])}

def run_projection(inputs: ProjectionInputs, tables: ModelTables, ft: ForwardTables, as_of_date: date,
                   inflation=None, curve=None, legacy_quirks: bool = True, feed_years: int | None = DASHBOARD_FEED_YEARS,
                   focus_year: int | None = None, **kw) -> tuple[pd.DataFrame, dict]:
    """Full projection (spec API): returns (DataFrame keyed by Excel column code, summary dict).

    Extra column `UNFUNDED` (not in Excel) = shortfall left after all accounts are exhausted.
    """
    df, meta = run_through_phase3(inputs, tables, ft, as_of_date, inflation, curve, legacy_quirks, **kw)
    back = run_backward(inputs, df, feed_years)
    df = pd.concat([df, back], axis=1)
    df["UNFUNDED"] = np.maximum(-df["CD"] - df["CQ"], 0.0)
    summary = build_summary(inputs, df)
    summary.update({k: meta[k] for k in ("inflation_id", "curve_id", "curve_method", "legacy_quirks", "valuation_date")})
    summary["as_of_date"] = str(as_of_date)
    summary["first_unfunded_year"] = (int(df.loc[df["UNFUNDED"] > 0.005, "B"].iloc[0])
                                      if (df["UNFUNDED"] > 0.005).any() else None)
    if focus_year is not None:
        summary["focus"] = dashboard_metrics(df, focus_year)
    return df, summary
