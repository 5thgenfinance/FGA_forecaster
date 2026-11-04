"""Phase 5 - scenario sweeps. Each sweep runs the full projection with modified inputs/assumptions, checks the
structural invariants and a documented directional expectation against the baseline.

There is no Excel reference for these cases (the workbook would have to be recalculated per case - see
reference_io.export_case); the expectations are economic/actuarial sanity checks, not parity tests.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Callable
import numpy as np
import pandas as pd
from .engine import ModelTables
from .inputs import ProjectionInputs
from .loop import ForwardTables
from .parity import check_invariants
from .pv import run_projection

Expect = Callable[[pd.DataFrame, dict, pd.DataFrame, dict], tuple]

@dataclass
class Sweep:
    name: str
    group: str
    overrides: dict = field(default_factory=dict)       # ProjectionInputs fields
    kwargs: dict = field(default_factory=dict)          # run_projection kwargs (draw_pct, cash_months, ...)
    curve_shift_bp: float = 0.0
    inflation_pair: tuple | None = None                 # (cpi_col, cola_col) from tblInflation
    expect: Expect | None = None
    note: str = ""

def _gt(col, idx=0, label=""):
    return lambda b, bs, d, s: (d[col].iloc[idx] > b[col].iloc[idx], f"{col}[{idx}] should rise vs baseline {label}")
def _lt(col, idx=0, label=""):
    return lambda b, bs, d, s: (d[col].iloc[idx] < b[col].iloc[idx], f"{col}[{idx}] should fall vs baseline {label}")
def _sum_gt(key):
    return lambda b, bs, d, s: (s[key] > bs[key], f"{key} should rise")
def _sum_lt(key):
    return lambda b, bs, d, s: (s[key] < bs[key], f"{key} should fall")
def _ratio(col, ratio, rel=1e-9):
    return lambda b, bs, d, s: (np.isclose(d[col].iloc[0] / b[col].iloc[0], ratio, rtol=rel), f"{col}[0] ratio should be {ratio:.6g}")
def _same(col, idx=0):
    return lambda b, bs, d, s: (np.isclose(d[col].iloc[idx], b[col].iloc[idx], rtol=1e-12), f"{col}[{idx}] should be unchanged")
def _all(*fs):
    def f(b, bs, d, s):
        msgs = [m for ok, m in (g(b, bs, d, s) for g in fs) if not ok]
        return (not msgs, "; ".join(msgs))
    return f

def default_sweeps() -> list[Sweep]:
    S = []
    S.append(Sweep("baseline", "baseline"))
    # retirement timing
    S.append(Sweep("retire_2yrs_later", "retirement date", {"t_ret_date": date(2031, 3, 28)}, expect=_gt("AF"), note="more salary years -> larger salary asset"))
    S.append(Sweep("retire_1yr_earlier", "retirement date", {"t_ret_date": date(2028, 3, 28)}, expect=_lt("AF")))
    # social security election age (PIA held constant -> benefit is NOT scaled for claiming age)
    for age in (62, 70):
        S.append(Sweep(f"ssi_age_{age}", "social security", {"SSI_ret_age": age},
                       expect=_gt("X") if age == 62 else _lt("X"),
                       note="SSI_PIA is not adjusted for claiming age; change it per election age"))
    S.append(Sweep("ssi_pia_plus_20pct", "social security", {"SSI_PIA": 3660}, expect=_gt("X")))
    # household
    S.append(Sweep("single_person", "household", {"s_dob": None, "t_s_ret_date": None}, expect=_lt("P"), note="single life < last-survivor of a couple"))
    S.append(Sweep("primary_disabled", "household", {"disabled": True}, expect=_lt("P")))
    S.append(Sweep("primary_female", "household", {"p_gender": "F"}))
    S.append(Sweep("already_retired", "household", {"retired": "RETIRED", "t_ret_date": date(2026, 1, 1), "salary": 0, "pre_401k": 0}))
    # spending and frequency flags
    S.append(Sweep("expenses_plus_20pct", "spending", {"net_expenses": 6000}, expect=_all(_ratio("P", 1.2), _sum_lt("funding_ratio"))))
    S.append(Sweep("expenses_flag_yearly", "spending", {"t_expenses": "Yearly"}, expect=_ratio("G", 1 / 12)))
    S.append(Sweep("no_mortgage", "spending", {"mortgage": 0}, expect=_same("P")))
    S.append(Sweep("long_mortgage_360", "spending", {"mort_payments": 360}, expect=_gt("H", 10)))
    # rates and curves
    S.append(Sweep("curve_plus_100bp", "discount curve", curve_shift_bp=100, expect=_all(_sum_lt("act_liabilities_C2"), _sum_lt("act_assets_C1"))))
    S.append(Sweep("curve_minus_100bp", "discount curve", curve_shift_bp=-100, expect=_all(_sum_gt("act_liabilities_C2"))))
    S.append(Sweep("hurdle_3pct", "discount curve", {"hurdle_rate": 0.03}, expect=_same("P"), note="hurdle only drives J/K (AK, BW); the liability P uses the curve"))
    S.append(Sweep("hurdle_8pct", "discount curve", {"hurdle_rate": 0.08}, expect=_same("P")))
    # inflation
    S.append(Sweep("inflation_load_plus_1pt", "inflation", {"InflationLoad": 0.035}, expect=_all(_gt("P"), _sum_lt("funding_ratio"))))
    for cpi, cola in (("CPI_74", "COLA_74"), ("Hist52", "Hist52"), ("CAGR30", "CAGR30")):
        S.append(Sweep(f"inflation_{cpi}", "inflation", {"InflationScenario": cpi, "COLAScenario": cola}, inflation_pair=(cpi, cola)))
    # policy parameters
    S.append(Sweep("ira_draw_0pct", "policy", kwargs={"draw_pct": 0.0}))
    S.append(Sweep("ira_draw_10pct", "policy", kwargs={"draw_pct": 0.10}))
    S.append(Sweep("cash_reserve_6mo", "policy", kwargs={"cash_months": 6}))
    S.append(Sweep("zero_assets_retire_now", "stress", {"pre_401k": 0, "pre_IRA": 0, "roth_IRA": 0, "brokerage": 225000, "real_estate": 0}))
    return S

def run_sweeps(tables: ModelTables, ft: ForwardTables, as_of: date, sweeps: list[Sweep] | None = None) -> pd.DataFrame:
    sweeps = sweeps or default_sweeps()
    base_inp = ProjectionInputs()
    base_df, base_sum = run_projection(base_inp, tables, ft, as_of)
    rows = []
    for sw in sweeps:
        try:
            inp = ProjectionInputs(**{**base_inp.model_dump(), **sw.overrides})
            curve = None
            if sw.curve_shift_bp:
                curve = tables.legacy_curve().with_spread(sw.curve_shift_bp / 1e4, id=f"legacy{sw.curve_shift_bp:+g}bp")
            infl = tables.legacy_inflation(*sw.inflation_pair) if sw.inflation_pair else None
            df, s = run_projection(inp, tables, ft, as_of, inflation=infl, curve=curve, **sw.kwargs)
            inv = check_invariants(df, s)
            ok, msg = (True, "")
            if sw.expect:
                ok, msg = sw.expect(base_df, base_sum, df, s)
            rows.append({"sweep": sw.name, "group": sw.group, "C1": s["act_assets_C1"], "C2": s["act_liabilities_C2"],
                         "C3": s["surplus_C3"], "funding_ratio": s["funding_ratio"], "peak_assets": s["peak_assets"],
                         "first_unfunded_year": s["first_unfunded_year"], "P1": df["P"].iloc[0], "X1": df["X"].iloc[0],
                         "AF1": df["AF"].iloc[0], "years": len(df), "invariants": "; ".join(inv) or "ok",
                         "expectation": "n/a" if not sw.expect else ("ok" if ok else f"FAIL: {msg}"), "note": sw.note})
        except Exception as e:                                # a sweep must never abort the whole run
            rows.append({"sweep": sw.name, "group": sw.group, "invariants": f"ERROR {type(e).__name__}: {e}",
                         "expectation": "ERROR", "note": sw.note})
    return pd.DataFrame(rows)

def sweeps_ok(results: pd.DataFrame) -> bool:
    return bool((results["invariants"] == "ok").all() and (~results["expectation"].str.startswith(("FAIL", "ERROR"))).all())
