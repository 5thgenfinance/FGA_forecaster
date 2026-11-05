"""Editable model tables. Originals in data/ are never modified; edits go to data_user/."""
from __future__ import annotations
import shutil, datetime as dt
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data"
USER = ROOT / "data_user"
TABLES = {  # label -> csv stem (rename here if your CSV names differ)
    "Inflation": "tblInflation", "Required minimum distribution divisors": "tblLURMD",
    "Tax brackets": "tblTax", "Capital gains tax": "tblLTGCtax",
    "Mortality": "tblMortality", "Discount rates": "tblDiscountRates",
    "Treasury curve": "TreasuryCurve",
}


def effective_dir() -> Path:
    """Folder the model should read: data_user if it exists, else data."""
    return USER if any(USER.glob("*.csv")) else BASE


def is_customised() -> bool:
    return effective_dir() == USER


def load(stem: str, original: bool = False) -> pd.DataFrame:
    p = (BASE if original or not is_customised() else USER) / f"{stem}.csv"
    return pd.read_csv(p)


def validate(stem: str, new: pd.DataFrame) -> list[str]:
    """Return a list of problems; empty means OK. Extra columns are allowed."""
    orig = load(stem, original=True)
    errs: list[str] = []
    missing = [c for c in orig.columns if c not in new.columns]
    if missing:
        return [f"Original columns cannot be removed: {missing}"]
    if new.columns.duplicated().any() or any(str(c).strip() == "" for c in new.columns):
        return ["Column names must be unique and not blank."]
    if len(new) == 0:
        return ["Table cannot be empty."]
    key = orig.columns[0]
    if new[key].isna().any():
        errs.append(f"Every row needs a value in '{key}'.")
    elif new[key].duplicated().any():
        errs.append(f"'{key}' values must be unique.")
    elif pd.api.types.is_numeric_dtype(orig[key]) and not new[key].is_monotonic_increasing:
        errs.append(f"'{key}' must be in increasing order.")
    for c in orig.columns:
        if pd.api.types.is_numeric_dtype(orig[c]):
            conv = pd.to_numeric(new[c], errors="coerce")
            bad = conv.isna() & new[c].notna()
            if bad.any():
                errs.append(f"'{c}' must be numeric (row {int(bad.idxmax()) + 1}).")
            elif (conv.dropna().abs() == float("inf")).any():
                errs.append(f"'{c}' has an infinite value.")
    if stem == "tblMortality":
        q = [c for c in orig.columns if c != key and pd.api.types.is_numeric_dtype(orig[c])]
        qq = new[q].apply(pd.to_numeric, errors="coerce")
        if ((qq < 0) | (qq > 1)).any().any():
            errs.append("Mortality rates must be between 0 and 1.")
    return errs


def extra_columns(stem: str, df: pd.DataFrame | None = None) -> list[str]:
    df = load(stem) if df is None else df
    orig = load(stem, original=True)
    return [c for c in df.columns if c not in orig.columns]


def save(stem: str, new: pd.DataFrame) -> Path:
    errs = validate(stem, new)
    if errs:
        raise ValueError("; ".join(errs))
    if not any(USER.glob("*.csv")):
        USER.mkdir(exist_ok=True)
        for f in BASE.glob("*"):
            if f.is_file():
                shutil.copy(f, USER / f.name)
    tgt = USER / f"{stem}.csv"
    if tgt.exists():
        bk = USER / "backups"; bk.mkdir(exist_ok=True)
        shutil.copy(tgt, bk / f"{stem}_{dt.datetime.now():%Y%m%d_%H%M%S}.csv")
    new.to_csv(tgt, index=False)
    return tgt


def add_column(stem: str, name: str, kind: str = "number", default=None) -> Path:
    """Add a column to the saved table (kind: 'number' or 'text'). Saves immediately."""
    name = (name or "").strip()
    df = load(stem)
    if not name:
        raise ValueError("Column name is required.")
    if name in df.columns:
        raise ValueError(f"Column '{name}' already exists.")
    if kind == "number":
        val = float(default) if default not in (None, "") else float("nan")
    else:
        val = "" if default is None else str(default)
    df[name] = val
    return save(stem, df)


def drop_column(stem: str, name: str) -> Path:
    """Remove an added column. Original columns cannot be dropped."""
    df = load(stem)
    if name not in extra_columns(stem, df):
        raise ValueError("Only columns you added can be removed.")
    return save(stem, df.drop(columns=[name]))


def reset(stem: str | None = None) -> None:
    """Reset one table (or all) to the original."""
    if stem is None:
        shutil.rmtree(USER, ignore_errors=True)
    elif (USER / f"{stem}.csv").exists():
        shutil.copy(BASE / f"{stem}.csv", USER / f"{stem}.csv")
