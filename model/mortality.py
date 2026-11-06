"""Survival curves: TPXCURVE, TPXCURVE_RP, EXPECTEDLIFE(_JOINT), PROJECTMORTALITY_RP."""
from __future__ import annotations
from datetime import date
import numpy as np
import pandas as pd
from .helpers import age_nearest, frasier, excel_round

class MortalityTable:
    """Wraps tblMortality (Age + qx columns). Lookups are exact-match (XLOOKUP)."""
    def __init__(self, df: pd.DataFrame):
        self.df = df.set_index("Age")
        self.max_age = int(df["Age"].max())

    def qx(self, col: str, ages: np.ndarray) -> np.ndarray:
        """qx for ages <= max_age; ages beyond the table return NaN (caller sets px=0)."""
        if col not in self.df.columns:
            raise KeyError(f"mortality column {col!r} not in table")
        out = np.full(len(ages), np.nan)
        for i, a in enumerate(ages):
            if a > self.max_age:
                continue
            if a not in self.df.index:
                raise KeyError(f"age {a} missing from mortality table")
            out[i] = self.df.at[a, col]
        return out

def _cum_px(q: np.ndarray, ages: np.ndarray, max_age: int, allow_blank: bool) -> np.ndarray:
    blank = (ages <= max_age) & np.isnan(q)
    if blank.any() and not allow_blank:
        raise ValueError(f"blank qx at ages {ages[blank].tolist()[:5]}; pass allow_blank=True for Excel parity (blank=0)")
    px = np.where(ages > max_age, 0.0, 1.0 - np.nan_to_num(q, nan=0.0))
    return np.cumprod(px)

def tpx_curve(tbl: MortalityTable, col: str, age: int, proj_duration: int, allow_blank=False) -> np.ndarray:
    """TPXCURVE: cumulative product of (1-qx); element 0 is 1-qx(age), as SCAN does in Excel."""
    ages = np.arange(age, age + max(1, proj_duration))
    return _cum_px(tbl.qx(col, ages), ages, tbl.max_age, allow_blank)

def tpx_curve_rp(tbl: MortalityTable, emp_col: str, ret_col: str, age: int, proj_duration: int,
                 years_to_ret: int, allow_blank=False) -> np.ndarray:
    """TPXCURVE_RP: employee qx before retirement (idx < years_to_ret), retiree qx afterwards."""
    idx = np.arange(max(1, proj_duration))
    ages = age + idx
    use_emp = idx < years_to_ret
    q = np.full(len(ages), np.nan)
    if use_emp.any():
        q[use_emp] = tbl.qx(emp_col, ages[use_emp])
    if (~use_emp).any():
        q[~use_emp] = tbl.qx(ret_col, ages[~use_emp])
    return _cum_px(q, ages, tbl.max_age, allow_blank)

def _sex_col(gender: str, male: str, female: str) -> str:
    g = gender.strip().upper()
    if g not in ("M", "F"):
        raise ValueError("gender must be M or F")
    return male if g == "M" else female

def expected_life(tbl: MortalityTable, male_col: str, female_col: str, gender: str, age: int) -> float:
    """EXPECTEDLIFE: sum of the survival curve from `age`."""
    col = _sex_col(gender, male_col, female_col)
    return float(tpx_curve(tbl, col, age, max(1, tbl.max_age - age)).sum())

def expected_life_joint(tbl: MortalityTable, male_col, female_col, gender_x, gender_y, age_x, age_y, status) -> float:
    """EXPECTEDLIFE_JOINT: sum of FRASIER(tpx, tpy, status)."""
    dur = max(1, tbl.max_age - age_x, tbl.max_age - age_y)
    tx = tpx_curve(tbl, _sex_col(gender_x, male_col, female_col), age_x, dur)
    ty = tpx_curve(tbl, _sex_col(gender_y, male_col, female_col), age_y, dur)
    return float(frasier(tx, ty, status).sum())

def _cols(prefix: str, sex: str, phase: str) -> tuple[str, str]:
    """(pre-retirement column, post-retirement column). Non-RP tables have one column for both."""
    p = prefix.replace(" ", "")              # tolerate "IAM 2012" in old client files
    if p.upper().startswith("RP"):
        return f"{p}{sex}E", f"{p}{sex}{phase}"
    c = f"{p}{sex}"
    return c, c


def project_mortality_rp(tbl: MortalityTable, proj_duration: int, status: str, is_joint: bool, prefix: str,
                         p_dob: date, s_dob, p_gender: str, disabled: bool,
                         as_of: date, t_ret_date: date, allow_blank: bool = False) -> np.ndarray:
    """PROJECTMORTALITY_RP (Projection!I). `as_of` must be ASOFDATE(): t_ret_date when PRERET, today when RETIRED."""
    age_x = age_nearest(p_dob, as_of)
    p_sex = "M" if p_gender.strip().upper() == "M" else "F"
    s_sex = "F" if p_sex == "M" else "M"
    yrs_to_ret = max(0, int(excel_round((t_ret_date - as_of).days / 365.25, 0)))
    ph = "D" if disabled else "H"
    tpx = tpx_curve_rp(tbl, *_cols(prefix, p_sex, ph), age_x, proj_duration, yrs_to_ret, allow_blank)
    if not is_joint:
        return tpx
    age_y = age_nearest(s_dob, as_of)
    tpy = tpx_curve_rp(tbl, *_cols(prefix, s_sex, "H"), age_y, proj_duration, 0, allow_blank)
    return frasier(tpx, tpy, status)
