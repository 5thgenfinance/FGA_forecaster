"""Phase 0 export: python export_workbook.py RMIF.xlsx data/"""
import sys, pandas as pd
from openpyxl import load_workbook
TABLES = {  # name: (sheet, range, expected_cols)
 "tblInflation": ("Inflation","A5:G69",["ForecastYr","CPI_74","Hist52","CAGR30","COLA_74","CPI70","COLA70"]),
 "tblLURMD": ("StaticParms","A3:B52",["attained_age","factor"]),
 "tblTax": ("StaticParms","J2:L8",["Rate","Single","MFJ"]),
 "tblLTGCtax": ("StaticParms","N2:R5",["Rate Min","Single","MFJ","Head of household","MFS"]),
 "tblMortality": ("Mortality","A4:I125",["Age","IAM2012M","IAM2012F","RP-2014ME","RP-2014FE","RP-2014MH","RP-2014FH","RP-2014MD","RP-2014FD"]),
 "tblDiscountRates": ("Discounting","A3:H67",["Year","Hurdle","ExpenseDiscountRt","SSIDiscountRt","EmploymentDiscountRt","ExpDiscFact","SSIDiscFact","EmpDiscFact"]),
 "TreasuryCurve": ("Calc","A1:D9",None),
}
def main(xlsx, out):
    wb = load_workbook(xlsx, data_only=True)
    for name,(sheet,rng,cols) in TABLES.items():
        rows = [[c.value for c in r] for r in wb[sheet][rng]]
        df = pd.DataFrame(rows[1:], columns=[str(c) for c in rows[0]])
        if cols and list(df.columns)!=cols: print(f"WARN {name}: headers {list(df.columns)}")
        if df.isna().all(axis=1).any(): print(f"WARN {name}: blank rows")
        df.to_csv(f"{out}/{name}.csv", index=False); print(name, df.shape)
if __name__=="__main__": main(*sys.argv[1:3])
