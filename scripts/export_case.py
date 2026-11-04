"""Export a reference case (inputs + cached Projection values + KPIs) from a recalculated workbook.

Usage: python scripts/export_case.py reference/FGA_Client_Onboarding_Calculator.xlsx reference_cases/retire_2031 \
           --as-of 2026-11-03 [--name retire_2031] [--focus-year 2040]
--as-of must be the date the workbook was last recalculated (TODAY() sets the projection length).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from datetime import date
from model.reference_io import export_case

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("xlsx"); ap.add_argument("folder")
    ap.add_argument("--as-of", required=True); ap.add_argument("--name"); ap.add_argument("--focus-year", type=int)
    a = ap.parse_args()
    f = export_case(a.xlsx, a.folder, date.fromisoformat(a.as_of), a.name, a.focus_year)
    print(f"Case written to {f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
