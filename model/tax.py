"""Ports of TaxEst, IraFill, ROTH_LIMIT, SLEEVEFEE, SS_AIME, SS_PIA, FORECASTSSI."""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import pandas as pd
from . import config as C

class TaxTables:
    """Wraps tblTax and tblLTGCtax (CSV exports)."""
    def __init__(self, tbl_tax: pd.DataFrame, tbl_ltgc: pd.DataFrame):
        self.rates = tbl_tax["Rate"].to_numpy(float)
        self.ord = {"Single": tbl_tax["Single"].to_numpy(float), "MFJ": tbl_tax["MFJ"].to_numpy(float)}
        self.lt = {"Single": tbl_ltgc["Single"].to_numpy(float), "MFJ": tbl_ltgc["MFJ"].to_numpy(float)}

    @classmethod
    def from_csv_dir(cls, path):
        p = Path(path)
        return cls(pd.read_csv(p / "tblTax.csv"), pd.read_csv(p / "tblLTGCtax.csv"))

def tax_est(t: TaxTables, ord_inc, ltcg_inc, is_joint, cola_rate, yrs_out) -> float:
    """TaxEst: ordinary brackets + LTCG 0/15/20% + NIIT; thresholds indexed by (1+cola)^yrs."""
    idx = (1 + cola_rate) ** yrs_out
    key = "MFJ" if is_joint else "Single"
    std = (C.STD_DED_MFJ if is_joint else C.STD_DED_SINGLE) * idx
    starts = np.concatenate([[0.0], t.ord[key] * idx])
    rates = np.concatenate([[C.BASE_ORDINARY_RATE], t.rates])
    ends = np.concatenate([starts[1:], [1e99]])
    total_taxable = max(0.0, ord_inc + ltcg_inc - std)
    ord_taxable = min(total_taxable, max(0.0, ord_inc - std))
    gain_taxable = total_taxable - ord_taxable
    ord_tax = float(np.sum(rates * (ord_taxable > starts) * (np.minimum(ord_taxable, ends) - starts)))
    lim = t.lt[key] * idx
    top0, top15 = lim[0], lim[1]
    top = ord_taxable + gain_taxable
    g0 = max(0.0, min(top, top0) - ord_taxable)
    g15 = max(0.0, min(top, top15) - max(ord_taxable, top0))
    g20 = gain_taxable - g0 - g15
    thr = C.NIIT_THRESHOLD_MFJ if is_joint else C.NIIT_THRESHOLD_SINGLE
    niit = C.NIIT_RATE * min(ltcg_inc, max(0.0, ord_inc + ltcg_inc - thr))
    return ord_tax + C.LTCG_RATE_15 * g15 + C.LTCG_RATE_20 * g20 + niit

def ira_fill(t: TaxTables, ord_inc, ltcg_inc, is_joint, cola_rate, yrs_out, ira_bal, target_sel) -> float:
    """IraFill: trad-IRA headroom to fill the 12% bracket (target_sel=2) or the 0% LTCG band."""
    idx = (1 + cola_rate) ** yrs_out
    key = "MFJ" if is_joint else "Single"
    std = (C.STD_DED_MFJ if is_joint else C.STD_DED_SINGLE) * idx
    lt_top0 = t.lt[key][0] * idx
    br_top12 = t.ord[key][1] * idx  # 2nd row of tblTax = start of 22% = top of 12%
    room_lt = lt_top0 + std - ord_inc - ltcg_inc
    room_br = br_top12 + std - ord_inc
    room = room_br if target_sel == 2 else room_lt
    return min(ira_bal, max(0.0, room))

def _floor(x, sig): return math.floor(x / sig + 1e-12) * sig
def _ceil(x, sig): return math.ceil(x / sig - 1e-12) * sig

def roth_limit(income, joint, p_age, s_age, yrs=0, infl=C.ROTH_INFLATION_DEFAULT) -> float:
    """ROTH_LIMIT: contribution limit with catch-up, MAGI phase-out, indexing; capped at earned income."""
    f = (1 + infl) ** yrs
    base = max(C.ROTH_BASE, _floor(C.ROTH_BASE * f, 500))
    cu = max(C.ROTH_CATCHUP, _floor(C.ROTH_CATCHUP * f, 100))
    lo0 = C.ROTH_PHASEOUT_LO_MFJ if joint else C.ROTH_PHASEOUT_LO_SINGLE
    rg0 = C.ROTH_RANGE_MFJ if joint else C.ROTH_RANGE_SINGLE
    lo = max(lo0, _floor(lo0 * f, 1000))
    rng = max(rg0, _floor(rg0 * f, 1000))
    hi = lo + rng
    def amt(age):
        L = base + (cu if age >= C.ROTH_CATCHUP_AGE else 0)
        if income <= lo: return L
        if income >= hi: return 0
        return min(L, max(200, _ceil(L * (hi - income) / rng, 10)))
    tot = amt(p_age) + amt(s_age) if joint else amt(p_age)
    return min(tot, max(income, 0))

def sleeve_fee(sleeve, aum) -> float:
    """SLEEVEFEE: tiered advisory fee for sleeves 1-5."""
    if sleeve != int(sleeve) or not 1 <= sleeve <= 5 or aum < 0:
        raise ValueError("invalid sleeve/aum (Excel #N/A)")
    b1, b2 = C.FEE_TIER_BREAKS
    tiers = (min(aum, b1), max(min(aum, b2) - b1, 0), max(aum - b2, 0))
    return sum(a * r for a, r in zip(tiers, C.FEE_SCHEDULE[int(sleeve)]))

def ss_aime(indexed_earnings) -> int:
    """SS_AIME: top-35 indexed earnings / 420, rounded down."""
    top = sorted(indexed_earnings, reverse=True)[:35]
    return math.floor(sum(top) / 420)

def ss_pia(aime, bend1, bend2) -> float:
    """SS_PIA: 90/32/15% bend-point formula, floored to $0.10."""
    x = round(0.9 * min(aime, bend1) + 0.32 * max(min(aime, bend2) - bend1, 0) + 0.15 * max(aime - bend2, 0), 4)
    return math.floor(x * 10 + 1e-9) / 10

def forecast_ssi(ages, cola_factors, ssi_ret_age, ssi_pia, ssi_freq) -> np.ndarray:
    """FORECASTSSI: zero before election age, then PIA grown by cumulative PRIOR-year COLA.
    `cola_factors` are factors (1.02), i.e. Projection column Q, not fractions."""
    annual = ssi_pia * 12 if ssi_freq == "Monthly" else ssi_pia
    ages, cola = np.asarray(ages, float), np.asarray(cola_factors, float)
    prior = np.concatenate([[1.0], np.cumprod(cola)[:-1]])
    return np.where(ages >= ssi_ret_age, annual * prior, 0.0)
