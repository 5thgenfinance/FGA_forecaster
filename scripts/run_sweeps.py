"""Run scenario sweeps (retirement date, SSI age, household, spending, curves, inflation, policy).

Usage: python scripts/run_sweeps.py [--data data] [--as-of 2026-11-03] [--out results/sweeps.csv]
Exit code 1 if any invariant or directional expectation fails.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from datetime import date
import pandas as pd
from model.engine import ModelTables
from model.loop import ForwardTables
from model.sweeps import run_sweeps, sweeps_ok

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="data")
    ap.add_argument("--as-of", default="2026-11-03")
    ap.add_argument("--out", default="results/sweeps.csv")
    a = ap.parse_args()
    res = run_sweeps(ModelTables.from_csv_dir(a.data), ForwardTables.from_csv_dir(a.data), date.fromisoformat(a.as_of))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(a.out, index=False)
    pd.set_option("display.width", 200)
    show = res[["sweep", "funding_ratio", "C3", "first_unfunded_year", "invariants", "expectation"]].copy()
    show["funding_ratio"] = show["funding_ratio"].round(3); show["C3"] = show["C3"].round(0)
    print(show.to_string(index=False))
    ok = sweeps_ok(res)
    print("\nALL SWEEPS OK" if ok else "\nSWEEP FAILURES - see the invariants/expectation columns")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
