"""Phase 2 - vector stage of the projection engine (Excel 'Projection' sheet, Phase A columns).

Columns that do not depend on account balances: timeline A-D, inflation E-F, expenses G-H,
survivorship I, discounting J-O, reserve P, COLA/SSI Q-Y, salary Z-AG, mortgage BP-BT.
Excel column codes are used as DataFrame column names for cell-by-cell comparison.
Assumption objects (InflationScenario, DiscountCurve) are passed in; nothing is read from module state.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
from .curves import DiscountCurve
from .helpers import (age_nearest, as_of_valuation_date, monthly_payment, mtg_bal_eoy,
                      proj_length, time_factor, work_incur)
from .inputs import ProjectionInputs
from .mortality import MortalityTable, project_mortality_rp
from .scenarios import InflationScenario
from .tax import forecast_ssi

MAX_HORIZON = 64
K_FLOOR = 1e-8            # Projection!K7
BT_LEGACY_DIVISOR_YEARS = range(2, 13)   # Projection!BT8:BT18 divide by prior-row BR (spec issue #7)

VECTOR_COLUMNS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
                  "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC", "AD", "AE", "AF", "AG",
                  "BP", "BQ", "BR", "BS", "BT"]

@dataclass
class ModelTables:
    """Reference tables exported in Phase 0."""
    mortality: MortalityTable
    inflation_table: pd.DataFrame
    treasury: pd.DataFrame

    @classmethod
    def from_csv_dir(cls, path) -> "ModelTables":
        p = Path(path)
        return cls(MortalityTable(pd.read_csv(p / "tblMortality.csv")),
                   pd.read_csv(p / "tblInflation.csv"), pd.read_csv(p / "TreasuryCurve.csv"))

    def legacy_inflation(self, cpi_col: str, cola_col: str) -> inflation_scenario:
        for c in (cpi_col, cola_col):
            if c not in self.inflation_table.columns:
                raise KeyError(f"inflation scenario {c!r} not in tblInflation")
        return InflationScenario.from_legacy_table(self.inflation_table, cpi_col, cola_col)

    def legacy_curve(self) -> DiscountCurve:
        return DiscountCurve.from_df(self.treasury, "legacy_treasury")

def build_discount_table(curve: DiscountCurve, employment_spread: float, n: int = MAX_HORIZON) -> pd.DataFrame:
    """Rebuilds Discounting!tblDiscountRates from a curve.

    Rates are TREASURYRATE(year) (+ spread for employment). Mid-year factors apply the same
    FORECAST.LINEAR regression to the *table's own* rate column (as TREASURYDISC does in Excel).
    """
    yrs = np.arange(1, n + 1, dtype=float)
    exp = np.array([curve.rate(y) for y in yrs])
    ssi = exp.copy()
    emp = exp + employment_spread
    def mid(rates):
        c = DiscountCurve("tbl", tuple(yrs), tuple(rates), method=curve.method)
        return np.array([c.disc(y, "MID") for y in yrs])
    return pd.DataFrame({"Year": yrs.astype(int), "ExpenseDiscountRt": exp, "SSIDiscountRt": ssi,
                         "EmploymentDiscountRt": emp, "ExpDiscFact": mid(exp), "SSIDiscFact": mid(ssi),
                         "EmpDiscFact": mid(emp)})

def _eoy_disc(years: np.ndarray, table_years: np.ndarray, rates: np.ndarray, method: str) -> np.ndarray:
    c = DiscountCurve("tbl", tuple(table_years.astype(float)), tuple(rates), method=method)
    return np.array([c.disc(float(y), "EOY") for y in years])

def _suffix_sum(x: np.ndarray) -> np.ndarray:
    """SUM(x[t]:x[end]) for every t."""
    return np.cumsum(x[::-1])[::-1]

def _pv_reserve(flow: np.ndarray, annuity_end: np.ndarray) -> np.ndarray:
    """Year 1: SUM(flow). Year t>=2: SUM(flow[t:]) / annuity_end[t-1], 0 if that divisor is 0."""
    s = _suffix_sum(flow)
    out = np.zeros_like(s)
    out[0] = s[0]
    for t in range(1, len(s)):
        out[t] = 0.0 if annuity_end[t - 1] == 0 else s[t] / annuity_end[t - 1]
    return out

def _mid_surv(i: np.ndarray) -> np.ndarray:
    """Mid-year survivorship: SQRT(I1); SQRT(I_t * I_{t-1})."""
    out = np.empty_like(i)
    out[0] = np.sqrt(i[0])
    out[1:] = np.sqrt(i[1:] * i[:-1])
    return out

def run_vectors(inputs: ProjectionInputs, tables: ModelTables, as_of_date: date,
                inflation: inflation_scenario | None = None, curve: DiscountCurve | None = None,
                legacy_quirks: bool = True, allow_blank_qx: bool = False) -> tuple[pd.DataFrame, dict]:
    """Return (DataFrame of Phase-A columns keyed by Excel column code, metadata dict).

    as_of_date plays the role of TODAY(): it sets the projection length (PROJLENGTH) and, if
    inputs.retired == 'RETIRED', the mortality valuation date (ASOFDATE).
    legacy_quirks=True reproduces Projection!BT's inconsistent divisors (issue #7).
    """
    inflation = inflation or tables.legacy_inflation(inputs.inflation_scenario, inputs.cola_scenario)
    curve = curve or tables.legacy_curve()
    mort = tables.mortality
    dobs = [inputs.primary_dob] + ([inputs.spouse_dob] if inputs.joint else [])
    n = min(MAX_HORIZON, proj_length(mort.max_age, dobs, as_of_date))
    if n > len(inflation.cpi):
        raise ValueError(f"inflation scenario {inflation.id!r} covers {len(inflation.cpi)} years; {n} required")

    A = np.arange(1, n + 1)
    B = inputs.first_proj_year + A - 1
    C = np.array([age_nearest(inputs.primary_dob, date(int(y), 12, 31)) for y in B], float)
    D = (np.array([age_nearest(inputs.spouse_dob, date(int(y), 12, 31)) for y in B], float)
         if inputs.joint else np.full(n, np.nan))

    # inflation, expenses
    E = inflation.expense_factors(inputs.inflation_load, n)
    F = np.cumprod(E)
    G = time_factor(inputs.expenses_freq) * inputs.net_expenses * F       # G1=base*E1, Gt=G(t-1)*Et

    # mortgage (BP/BQ feed H)
    pmt = monthly_payment(inputs.mortgage, inputs.mortgage_rate, inputs.mortgage_payments_left)
    BP = np.array([mtg_bal_eoy(inputs.mortgage, inputs.mortgage_rate, pmt, int(a)) for a in A])
    prior_bp = np.concatenate([[inputs.mortgage], BP[:-1]])
    BQ = np.where(prior_bp > 1, pmt * 12, 0.0)
    H = BQ.copy()

    # survivorship + discounting
    asof = as_of_valuation_date(inputs.ret_status, inputs.primary_target_ret_date, as_of_date)
    I = project_mortality_rp(mort, n, "last_survivor", inputs.joint, inputs.mortality_table, inputs.primary_dob,
                             inputs.spouse_dob, inputs.p_gender, inputs.primary_disabled, asof, inputs.primary_target_ret_date,
                             allow_blank=allow_blank_qx)
    J = inputs.discount_rate ** A.astype(float)
    K = I * J
    K[0] = max(K[0], K_FLOOR)

    dt = build_discount_table(curve, inputs.employment_risk_spread)
    ty = dt["Year"].to_numpy()
    L = dt["ExpDiscFact"].to_numpy()[A - 1]
    S = dt["SSIDiscFact"].to_numpy()[A - 1]
    Z = dt["EmpDiscFact"].to_numpy()[A - 1]
    M = _mid_surv(I); T = M.copy(); AA = M.copy()
    N = _eoy_disc(A, ty, dt["ExpenseDiscountRt"].to_numpy(), curve.method) * I
    U = _eoy_disc(A, ty, dt["SSIDiscountRt"].to_numpy(), curve.method) * I
    AB = _eoy_disc(A, ty, dt["EmploymentDiscountRt"].to_numpy(), curve.method) * I

    O = L * G * M
    P = _pv_reserve(O, N)

    # SSI
    Q = inflation.cola_factors(n)
    R = np.cumprod(Q)
    V = forecast_ssi(C, Q, inputs.ssi_claim_age, inputs.ssi_pia, inputs.ssi_pia_freq)
    W = V * S * T
    X = _pv_reserve(W, U)
    Y = X - P

    # salary
    AG = np.array([work_incur(int(y), inputs.primary_target_ret_date) for y in B])
    sq = np.sqrt(Q)
    AC = np.zeros(n)
    post = time_factor(inputs.post_ret_income_freq) * inputs.post_ret_income
    for t in range(n):
        if AG[t] > 0:
            base = time_factor(inputs.salary_freq) * inputs.salary * AG[t] if t == 0 else AC[t - 1] * AG[t]
        else:
            base = post
        AC[t] = base * sq[t]
    AD = time_factor(inputs.supp_salary_freq) * inputs.supp_salary * np.cumprod(sq)
    AE = (AC + AD) * AA * Z
    AF = _pv_reserve(AE, AB)

    # mortgage PV
    BR = _eoy_disc(A, ty, dt["ExpenseDiscountRt"].to_numpy(), curve.method)
    BS = BR * BQ
    s = _suffix_sum(BS)
    BT = s.copy()
    for t in range(1, n):
        divide = (t + 1) in BT_LEGACY_DIVISOR_YEARS if legacy_quirks else True
        if divide:
            BT[t] = s[t] / BR[t - 1]

    df = pd.DataFrame({"A": A, "B": B, "C": C, "D": D, "E": E, "F": F, "G": G, "H": H, "I": I, "J": J, "K": K,
                       "L": L, "M": M, "N": N, "O": O, "P": P, "Q": Q, "R": R, "S": S, "T": T, "U": U, "V": V,
                       "W": W, "X": X, "Y": Y, "Z": Z, "AA": AA, "AB": AB, "AC": AC, "AD": AD, "AE": AE,
                       "AF": AF, "AG": AG, "BP": BP, "BQ": BQ, "BR": BR, "BS": BS, "BT": BT})[VECTOR_COLUMNS]
    meta = {"n_years": n, "as_of_date": str(as_of_date), "valuation_date": str(asof),
            "inflation_id": inflation.id, "curve_id": curve.id, "curve_method": curve.method,
            "legacy_quirks": legacy_quirks, "monthly_mortgage_payment": pmt,
            "reserve_P1": float(P[0]), "ssi_asset_X1": float(X[0]), "salary_asset_AF1": float(AF[0]),
            "mortgage_pv_BT1": float(BT[0])}
    return df, meta
