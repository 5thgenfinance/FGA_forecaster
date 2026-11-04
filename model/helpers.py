"""Ports of the Excel LAMBDAs for dates, mortgage, RMD and misc helpers."""
from __future__ import annotations
import calendar, math
from datetime import date
import numpy as np

def _safe_date(y: int, m: int, d: int) -> date:
    """Excel DATE() rolls Feb 29 in a non-leap year to Mar 1."""
    try:
        return date(y, m, d)
    except ValueError:
        return date(y, 3, 1)

def edate(d: date, months: int) -> date:
    """Excel EDATE: clamps the day to month end."""
    y, m = divmod(d.year * 12 + d.month - 1 + months, 12)
    m += 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))

def attained_age(dob: date, as_of: date) -> int:
    """ATTAINEDAGE / DATEDIF(dob, date, 'y'): completed years."""
    if as_of < dob:
        raise ValueError("as_of precedes dob (Excel DATEDIF returns #NUM!)")
    return as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))

def age_nearest(dob: date, as_of: date) -> int:
    """AGENEAREST: age at nearest birthday."""
    this_year = _safe_date(as_of.year, dob.month, dob.day)
    last = _safe_date(as_of.year - (1 if this_year > as_of else 0), dob.month, dob.day)
    nxt = edate(last, 12)
    since, to_next = (as_of - last).days, (nxt - as_of).days
    return attained_age(dob, as_of) + (1 if to_next < since else 0)

def as_of_valuation_date(retired: str, t_ret_date: date, today: date) -> date:
    """ASOFDATE: today if RETIRED, else target retirement date."""
    return today if retired == "RETIRED" else t_ret_date

def retire_age(dob: date | None, ret_date: date | None) -> int:
    """RETIREAGE; raises ValueError where Excel returns #N/A."""
    if dob is None or ret_date is None or ret_date < dob:
        raise ValueError("invalid dob/ret_date")
    return attained_age(dob, ret_date)

def work_incur(yr: int, retire_date: date) -> float:
    """WORKINCUR: fraction of calendar year worked before retire_date, clipped to [0, 1]."""
    start, end = date(yr, 1, 1), date(yr + 1, 1, 1)
    return float(min(1.0, max(0.0, (retire_date - start).days / (end - start).days)))

def mtg_bal_eoy(principal: float, annual_rate: float, pmt: float, year: float) -> float:
    """MTGBALEOY: end-of-year balance, floored at zero. pmt is MONTHLY."""
    r, n = annual_rate / 12, year * 12
    bal = principal - pmt * n if r == 0 else principal * (1 + r) ** n - pmt * ((1 + r) ** n - 1) / r
    return max(0.0, bal)

def monthly_payment(principal: float, annual_rate: float, n_payments: int) -> float:
    """-PMT(rate/12, n, principal, 0)."""
    r = annual_rate / 12
    if n_payments <= 0 or principal == 0:
        return 0.0
    return principal / n_payments if r == 0 else principal * r / (1 - (1 + r) ** -n_payments)

def pretax_draw(budget: float, balance: float, draw_pct: float, is_elig) -> float:
    """PreTaxDraw = elig * MAX(0, MIN(budget, draw% * balance, balance))."""
    return float(is_elig) * max(0.0, min(budget, draw_pct * balance, balance))

def frasier(tpx, tpy, status: str):
    """FRASIER: 'joint' = px*py; 'last'/'last_survivor'/'last survivor' = px+py-px*py."""
    s = status.strip().lower()
    tpx, tpy = np.asarray(tpx, float), np.asarray(tpy, float)
    joint = tpx * tpy
    if s == "joint":
        return joint
    if s in ("last", "last_survivor", "last survivor"):
        return tpx + tpy - joint
    raise ValueError(f"unknown status {status!r}")

def time_factor(frequency: str) -> int:
    """TimeFactor: 12 if 'Monthly' else 1."""
    return 12 if frequency == "Monthly" else 1

def excel_round(x: float, digits: int = 0) -> float:
    """Excel ROUND: half away from zero."""
    f = 10 ** digits
    return math.copysign(math.floor(abs(x) * f + 0.5) / f, x)

def rmd(dob: date, calc_year: int, prior_year_end_balance: float, lurmd: dict) -> float:
    """RMD per IRS Uniform Lifetime table (StaticParms tblLURMD). `lurmd` maps age -> factor."""
    if prior_year_end_balance < 0:
        raise ValueError("negative balance (Excel #N/A)")
    age = calc_year - dob.year
    start = 72 if dob < date(1951, 1, 1) else 73 if dob < date(1960, 1, 1) else 75
    if age < start:
        return 0.0
    factor = 2.0 if age >= 120 else lurmd.get(age)
    if factor is None:
        raise KeyError(f"RMD factor missing for age {age}")
    return prior_year_end_balance / factor

def proj_length(max_age_in_table: int, dobs: list, as_of: date) -> int:
    """PROJLENGTH: max table age minus younger person's nearest age (min 1)."""
    return max(1, max_age_in_table - min(age_nearest(d, as_of) for d in dobs))
