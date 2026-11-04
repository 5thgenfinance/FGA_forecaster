"""Phase 0 export using the workbook's real Excel table refs.
python export_workbook.py FGA_Client_Onboarding_Calculator.xlsx data/"""
import sys, json, pandas as pd
from openpyxl import load_workbook
def main(xlsx, out):
    wb = load_workbook(xlsx, data_only=True); man = {}
    for ws in wb:
        for name, ref in ws.tables.items():
            rows = [[c.value for c in r] for r in ws[ref]]
            df = pd.DataFrame(rows[1:], columns=[str(c) for c in rows[0]])
            bad = [c for c in df.columns if df[c].astype(str).str.startswith("#").any()]
            if bad: print(f"WARN {name}: Excel errors in {bad}")
            df.to_csv(f"{out}/{name}.csv", index=False)
            man[name] = dict(sheet=ws.title, ref=ref, rows=len(df), nulls=int(df.isna().sum().sum()))
            print(name, ref, df.shape)
    json.dump(man, open(f"{out}/manifest.json", "w"), indent=1)
if __name__ == "__main__": main(*sys.argv[1:3])
