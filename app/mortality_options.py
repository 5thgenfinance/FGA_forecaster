"""Mortality table choices for the dropdown (Streamlit-independent)."""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

DEFAULT = "RP-2014"
# Names are the column PREFIXES used by the workbook: RP-2014 -> RP-2014ME/MH/MD..., IAM2012 -> IAM2012M / IAM2012F.
CANDIDATES = ["RP-2014"]
UNAVAILABLE = {"IAM2012"}          # shown greyed out and not selectable; remove from this set to enable it
MARKER = "(coming soon)"           # text the browser script looks for to grey an option


def option_label(opt: str) -> str:
    return f"{opt} {MARKER}" if opt in UNAVAILABLE else opt


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def available(columns, candidates=CANDIDATES) -> list[str]:
    cols = [_norm(c) for c in columns]
    return [c for c in candidates if any(_norm(c) in col for col in cols)]


def mortality_options(data_dir, current: str | None = None) -> list[str]:
    try:
        header = list(pd.read_csv(Path(data_dir) / "tblMortality.csv", nrows=0).columns)
    except (OSError, ValueError):
        header = []
    opts = available(header) or [DEFAULT]
    if current and current not in opts:
        opts.append(current)       # keep an imported value selectable instead of crashing
    return opts


def effective(selected: str) -> str:
    """The table the model really uses: unavailable choices fall back to the default."""
    return DEFAULT if selected in UNAVAILABLE else selected
