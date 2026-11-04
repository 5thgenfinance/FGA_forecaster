"""Compare the Python projection with cached Excel values for every reference case.

Usage (from the project root):
    python scripts/compare_to_excel.py [--cases reference_cases] [--data data] [--out results/parity] [--strict]
Exit code 0 = every case passes, 1 = at least one failure.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from model.engine import ModelTables
from model.loop import ForwardTables
from model.parity import discover_cases, run_all_cases, write_reports

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", default="reference_cases")
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="results/parity")
    ap.add_argument("--strict", action="store_true", help="abs 1e-6 (currency) / 1e-9 (factors), rel 1e-9")
    a = ap.parse_args()
    if not discover_cases(a.cases):
        print(f"No reference cases found in {a.cases}/ (each needs a case.json)."); return 1
    tables, ft = ModelTables.from_csv_dir(a.data), ForwardTables.from_csv_dir(a.data)
    results = run_all_cases(a.cases, tables, ft, strict=a.strict)
    write_reports(results, a.out)
    for r in results:
        c = r.columns
        worst = c[c["status"].isin(["PASS", "FAIL"])].sort_values("max_abs_diff", ascending=False).head(3)
        print(f"{r.name:<24} {'PASS' if r.passed else 'FAIL'}  columns pass={int((c.status == 'PASS').sum())} "
              f"fail={int((c.status == 'FAIL').sum())} missing={int((c.status == 'MISSING').sum())}  "
              f"summary fail={int((r.summary.status == 'FAIL').sum())}  invariants={len(r.invariants)}")
        for _, w in worst.iterrows():
            print(f"    largest diff {w['column']:>3}: abs {w['max_abs_diff']:.3g}  rel {w['max_rel_diff']:.3g}")
        for m in r.invariants:
            print("    INVARIANT:", m)
    print(f"Reports written to {a.out}/")
    return 0 if all(r.passed for r in results) else 1

if __name__ == "__main__":
    sys.exit(main())
