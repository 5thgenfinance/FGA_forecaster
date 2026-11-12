"""Shared helpers for the golden-master and rule tests (not collected as tests)."""
from __future__ import annotations
import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import numpy as np

from model.dashboard import build_report_data
from model.engine import ModelTables
from model.inputs import ProjectionInputs
from model.loop import ForwardTables

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
AS_OF = date(2026, 11, 6)          # fixed so results never depend on today's date

# Projection columns (Excel codes) that are saved for each case, and the rows kept.
KEY_COLUMNS = ["C", "E", "G", "I", "P", "X", "AF", "AK", "AM", "AO", "BV", "CD", "DH"]
KEY_ROWS = [0, 1, 2, 4, 9, 19, -1]

_tables = None


def tables():
    global _tables
    if _tables is None:
        _tables = (ModelTables.from_csv_dir(str(DATA_DIR)), ForwardTables.from_csv_dir(str(DATA_DIR)))
    return _tables


def make_inputs(overrides: dict | None = None) -> ProjectionInputs:
    """Defaults plus overrides. Dates may be given as ISO strings."""
    return ProjectionInputs(**(overrides or {}))


def run(overrides: dict | None = None, as_of: date = AS_OF):
    """Run the projection for defaults + overrides and return the report-data object (kpis, df, ...)."""
    mt, ft = tables()
    return build_report_data(make_inputs(overrides), mt, ft, as_of)


def _plain(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (str, type(None))):
        return value
    return str(value)


def summarize(rd) -> dict:
    """Small, stable snapshot of a run: the KPIs plus key columns at selected rows."""
    kpis = rd.kpis
    kpi_dict = dict(kpis) if isinstance(kpis, Mapping) or hasattr(kpis, "keys") else dict(vars(kpis))
    out = {"kpis": {k: _plain(v) for k, v in sorted(kpi_dict.items())}, "rows": len(rd.df)}
    cols = {}
    for c in KEY_COLUMNS:
        if c in rd.df.columns:
            series = rd.df[c].reset_index(drop=True)
            cols[c] = {str(i): _plain(series.iloc[i]) for i in KEY_ROWS if -len(series) <= i < len(series)}
            cols[c]["sum"] = _plain(series.apply(lambda v: v if isinstance(v, (int, float, np.number)) else np.nan).sum())
    out["columns"] = cols
    return out


def compare(actual, expected, path="", rtol=1e-9, atol=1e-6):
    """Recursively compare two summaries; returns a list of readable differences."""
    diffs = []
    if isinstance(expected, dict):
        for k in expected:
            if not isinstance(actual, dict) or k not in actual:
                diffs.append(f"{path}/{k}: missing in actual")
            else:
                diffs += compare(actual[k], expected[k], f"{path}/{k}", rtol, atol)
        for k in (actual if isinstance(actual, dict) else {}):
            if k not in expected:
                diffs.append(f"{path}/{k}: new in actual (not in golden file)")
    elif isinstance(expected, float) or isinstance(actual, float):
        if actual is None or expected is None:
            if actual != expected:
                diffs.append(f"{path}: {actual!r} != {expected!r}")
        elif not np.isclose(actual, expected, rtol=rtol, atol=atol):
            diffs.append(f"{path}: {actual!r} != {expected!r}")
    elif actual != expected:
        diffs.append(f"{path}: {actual!r} != {expected!r}")
    return diffs


def load_case(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf8"))
