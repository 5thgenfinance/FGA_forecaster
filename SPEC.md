# Retirement Model, Illustration and Forecasting Tool — Python Application Specification — Version 1.1
Generated from the workbook on 2026-11-03. Lines marked LIVE update from Excel. Version 1.1 amended 2026-11-07: sections 14 and the items marked [v1.1] are maintained by hand and are NOT regenerated from the workbook.

## Revision history
| Version | Date | Summary |
|---|---|---|
| 1.0 | 2026-11-03 | Original specification generated from the workbook (sections 0 to 13). |
| 1.1 | 2026-11-07 | Application-layer amendments made while building and testing the app: product branding and sticky header; Client details page with JSON save/load and tooltips; Income tax status as a PRE/POST choice; mortality-table handling (RP-2014 and the single-column IAM2012 convention, IAM2012 withheld from the dropdown); new Disposable income scenario slider; deployment and access notes; new known issues #15 to #17; updated acceptance-test notes. Calculation logic in sections 5, 8 and 9 is unchanged. |

Rules for this document: workbook-driven sections (3, 4, 8, 9, 10, 11) are regenerated from the workbook; the amendments marked [v1.1] and section 14 are not, and must be carried forward by hand when the sheet is regenerated.

## 0. Prompt for the AI coding assistant
You are a senior Python engineer with a strong understanding of pension actuarial science, retirement-income modeling, actuarial present values, mortality and survivorship, discounting, taxation, and retirement forecasting. Build version 1.0 of the application described below. Implement data loading and validation, helper functions, the year-by-year projection engine, dashboard outputs, CLI, optional Streamlit UI, and pytest tests. Preserve actuarial logic and terminology. Do not invent business rules: list ambiguities and propose defaults. Return a complete source tree, requirements.txt, README, sample input file, and test report.

## 1. Purpose and objective — Version 1.1
Version 1.1 (which extends version 1.0 without changing its calculations) is a retirement model, illustration and forecasting tool. It is designed to illustrate and forecast retirement funding outcomes for a primary person and optional spouse using pension actuarial concepts, including mortality and survivorship, actuarial present values, discounting, income commencement, taxes, required minimum distributions, contributions, and asset-depletion waterfalls.
The application projects retirement outcomes year by year, values expenses as a present-value liability, values Social Security, salary, investment income and account balances as assets, and reports funding status, surplus, cash flow, account balances and dashboard metrics. Results are illustrations and forecasts based on the selected assumptions; they are not guarantees.
The Excel workbook is the source of truth for the calculations. Python must reproduce its formulas, actuarial conventions and outputs within the tolerances in section 11. [v1.1] The application layer (branding, Client details page, scenario sliders, deployment) has no workbook equivalent and is specified in section 14.

## 2. Technical requirements
* Python 3.11+; numpy, pandas, pydantic or dataclasses, pytest; Plotly or matplotlib; optional Streamlit.
* No Excel/COM dependency at runtime. Export reference tables once to CSV from the workbook with openpyxl or pandas.
* Suggested modules: model/inputs.py, data.py, helpers.py, mortality.py, discounting.py, tax.py, engine.py, dashboard.py; app/cli.py, app/ui.py; tests/.
* Main API: run_projection(inputs, tables, as_of_date) -> (pandas.DataFrame, summary). Keep Excel column codes as DataFrame column names for cell-by-cell comparison.
* Expose as_of_date because TODAY() affects ages and projection length. Default to today; tests must pass a fixed date.
* Maximum horizon is 64 years; mortality ages are 0–120.

### 2.1 Excel semantics to reproduce
* DATEDIF(dob,date,'y') means completed years.
* FORECAST.LINEAR is ordinary least-squares regression over all supplied points, not nearest-point interpolation. TREASURYRATE and TREASURYDISC use this behavior; reproduce with numpy.polyfit.
* XLOOKUP is exact match. Raise an explicit validation error for missing keys.
* SCAN with multiplication is cumulative product (numpy.cumprod).
* Blank spouse DOB means single; blanks used in arithmetic behave as zero.
* Use NaN for Excel blank projection cells and 0 for dashboard-feed cells after the horizon.
* Percentages are stored as fractions: 0.05 means 5%.

## 3. Inputs — LIVE defaults from Main
Every row below is an editable and validated input in JSON/YAML, CLI, and UI. Dates use ISO yyyy-mm-dd.
| Label | Main cell | Defined name | Default |
|---|---|---|---|
| Primary DOB | Main!B4 | p_dob | 1969-03-28 |
| Spouse DOB | Main!B5 | s_dob | 1971-01-01 |
| Year | Main!B6 | cur_year | 2027 |
| Primary Target Ret Date | Main!B7 | t_ret_date | 2029-03-28 |
| Prim Ret Status | Main!B8 | retired | PRERET |
| Joint | Main!B9 | joint | TRUE |
| Secondary Target Ret Dt | Main!B10 | t_s_ret_date | 49031 |
| Primary Gender | Main!B12 | p_gender | M |
| Disabled | Main!B13 | disabled | FALSE |
| Mortality | Main!B14 | mort_table | RP-2014 (choice list; see 5.3 and 14.4) [v1.1] |
| Main Salary | Main!B17 | salary | 110000 |
| Sup Income | Main!B18 | sup_salary | 0 |
| Income Tax Status | Main!B19 | inc_tax_status | PRE (choice of PRE or POST) [v1.1] |
| Employment Risk Spread | Main!B20 | spread_emprisk | 0.015 |
| Post Retirement Income | Main!B21 | net_income | 0 |
| Net Expenses | Main!B22 | net_expenses | 5000 |
| Cash Cushion | Main!B23 | cash_cushion | 5 |
| Cash Cushion Amt | Main!B24 | cash_cushion_amt | 25000 |
| Inflation Scenario | Main!B25 | InflationScenario | CPI70 |
| Inflation Load | Main!B26 | InflationLoad | 0.025 (see known issue #15) |
| COLA | Main!B27 | COLAScenario | COLA70 |
| Pre 401k | Main!B30 | pre_401k | 47000 |
| Prim Trad IRA | Main!B32 | pre_IRA | 300000 |
| Roth IRA | Main!B34 | roth_IRA | 150000 |
| Mortgage | Main!C35 | mortgage | 150000 |
| Rate | Main!C36 | mort_rate | 0.03 |
| Remaining Pmts | Main!C37 | mort_payments | 60 |
| Brokerage Accts | Main!B40 | brokerage | 300000 |
| Real Estate | Main!B42 | real_estate | 400000 |
| SSI Elected Ret age | Main!B47 | SSI_ret_age | 67 |
| SSI PIA | Main!B49 | SSI_PIA | 3050 |
| Sleeve 3 Payment | Main!B52 | sup_income | 2000 |
| Sleeve 3 RoR | Main!B53 | sleeve3_ror | 0.14 |
| Sleeve 3 Growth | Main!B54 | sup_inc_irr | 0.04 |
| Sleeve 3 Deployed | Main!B55 | (unnamed) | 200000 |
| Hurdle Rate | Main!B62 | hurdle_rate | 0.05 |
| Discount Rate | Main!B64 | discount_rate | 0.952380952380952 |
| Long Term Asset RoR | Main!B65 | LTRoR | 0.125 |
| 401k Growth Rate MM | Main!B66 | growth_rt_401k | 0.035 |
| 401k Contribution Rate | Main!B67 | contrib_rt_401k | 0.14 |

[v1.1] Input-model notes:
* inc_tax_status is validated as a choice: "PRE" or "POST". Any other value is rejected, including on import of a saved client file.
* The model also holds inputs that are not listed in the table above because their defaults are zero or blank in the workbook: post_401k, s_pre_IRA, life_ins, other_PMs. They are editable in the UI and part of the JSON client file. life_ins is added to brokerage in BM5.
* client_name is metadata stored in the client file and shown in the dashboard heading. It is not a model input and does not affect any calculation.
* The model rejects unknown fields (extra fields forbidden) when a client file is loaded.

Derived and fixed rules:
* joint = spouse DOB is not blank. retired = RETIRED when retirement date is today/past, otherwise PRERET.
* discount_rate is a discount factor: 1/(1+hurdle_rate), then raised to the projection-year number.
* cur_year is the first projection year from Main!B6.
* Scenario selectors must match columns in tblInflation; mort_table must match mortality-table prefixes.
* Embedded constants should be centralized in config.py: mortgage remaining payments 12*5; SSI salary basis 3050*12; Roth/IRA/tax/NIIT/fee-tier constants from the LAMBDAs; BD draw 6%; cash reserve 2 months; Roth-limit inflation 3%.

## 4. Reference tables
Export these named tables to CSV:
* tblInflation — Inflation!A5:G69 — columns: ForecastYr, CPI_74, Hist52, CAGR30, COLA_74, CPI70, COLA70
* tblLURMD — StaticParms!A3:B52 — columns: attained_age, factor
* tblTax — StaticParms!J2:L8 — columns: Rate, Single, MFJ
* tblLTGCtax — StaticParms!N2:R5 — columns: Rate Min, Single, MFJ, Head of household, MFS
* tblMortality — Mortality!A4:I125 — columns: Age, IAM2012M, IAM2012F, RP-2014ME, RP-2014FE, RP-2014MH, RP-2014FH, RP-2014MD, RP-2014FD
* tblDiscountRates — Discounting!A3:H67 — columns: Year, Hurdle, ExpenseDiscountRt, SSIDiscountRt, EmploymentDiscountRt, ExpDiscFact, SSIDiscFact, EmpDiscFact
* TreasuryCurve — Calc!A1:D9 — columns: Year, Name, Spot Rate, Maturity

### 4.1 Tax tables — LIVE
tblTax: each row is a marginal rate starting at its displayed threshold. TaxEst prepends an implicit 10% bracket starting at zero.
| Rate | Single | MFJ |
|---|---|---|
| 0.12 | 12400 | 24800 |
| 0.22 | 50400 | 100800 |
| 0.24 | 105700 | 211400 |
| 0.32 | 201775 | 403550 |
| 0.35 | 256225 | 512450 |
| 0.37 | 640600 | 768700 |
tblLTGCtax:
| Rate | Single | MFJ | HOH | MFS |
|---|---|---|---|---|
| 0 | 49450 | 98900 | 66200 | 49450 |
| 0.15 | 545500 | 613700 | 579600 | 306850 |
| 0.2 | 545500 | 613700 | 579600 | 306850 |
The workbook currently has identical Single/MFJ thresholds in the 15% and 20% LTCG rows; preserve them for parity and flag them for review.

### 4.2 Treasury curve — LIVE
| Maturity year | Spot rate |
|---|---|
| 0.25 | 0.041029 |
| 0.5 | 0.042588 |
| 1 | 0.043298 |
| 2 | 0.045115 |
| 5 | 0.046378 |
| 10 | 0.048512 |
| 20 | 0.052783 |
| 30 | 0.052475 |

## 5. Architecture and calculation order
### 5.1 Discounting table
* Build 64 rows, Year 1..64. ExpenseDiscountRt = TREASURYRATE(year); SSIDiscountRt is the same; EmploymentDiscountRt adds spread_emprisk.
* Discount factors use 1/(1+r)^t with midpoint t=max(0, year-0.5), where r is FORECAST.LINEAR(t, rate column, year column).
### 5.2 Projection phases
* Phase A — vectors independent of balances: timeline A:D, inflation E:F, expenses G:H, survivorship I, discounting J:O, reserve P, COLA/SSI Q:Y, salary Z:AG, mortgage BP:BS/BQ.
* Phase B — forward loop: AI; AV/AW/AZ/BA; AX/BB; AM; AN; AO; BD/BE; BY; BZ; CA; CD; CF:CH; CJ:CO; balances AT/AU/AY/BI:BN/BV/BW.
* Phase C — backward PV calculations: AJ, AK, AQ, AR, BT, CC, CQ, CR, dashboard feed CW:DJ, and summary C1:C3/F2:F3.
* Important dependency: AI uses prior-row BK, so AK depends on the complete forward path.
### 5.3 Mortality
* [v1.1] Column naming is centralised in one helper, _cols(prefix, sex, phase), returning (pre-retirement column, post-retirement column). For tables whose prefix starts with RP it returns <prefix><sex>E and <prefix><sex><phase> (phase H healthy or D disabled), exactly as PROJECTMORTALITY_RP. For other tables (IAM2012) the table has one column per sex, <prefix>M or <prefix>F, and the same column is used before and after retirement; the disabled flag has no effect. Spaces in a prefix are ignored so older client files still load. Output for RP-2014 must remain identical to the workbook.
* PROJECTMORTALITY_RP creates primary and spouse survival curves and combines them with FRASIER: last survivor = px+py-px*py; joint = px*py.
* ASOFDATE is today when retired, otherwise retirement date. Use AGENEAREST. Primary transitions from employee to healthy/disabled qx; spouse effectively uses healthy after the first index.
* px=1-qx through table maximum and 0 beyond; survival is cumulative product, starting at 1.

## 6. Outputs and KPIs
* C1 Act Assets = X7 + AK7 + BW7. C2 Act Liabilities = P7. C3 plan surplus = C1-C2. Funding ratio = C1/C2.
* F2 balance-sheet assets = opening account balances. F3 liabilities = AQ4 + BP5.
* Preserve both surplus concepts: C3 includes SSI, NII and NPV of balances; yearly CC includes AK+X+AF-P, including salary but excluding balances.
* Dashboard focus-year metrics: total assets DH, net cash flow CX, age C, expenses G+H, SSI V, investment income AI.
* Milestones: first positive CX at/after retirement year; peak DH and its year; minimum DH where CW>0.
* Charts: line chart Year/CW vs Total Assets/DH and SOL Liability/DF; column chart Year/CW vs Net Cash Flow/CX.

## 7. CLI and Streamlit UI
* CLI example: python -m app.cli run --inputs inputs.json --as-of 2026-11-03 --out results/
* Write projection.csv, summary.json, and chart images. UI groups inputs into personal, income, expenses, accounts, mortgage, SSI, Sleeve 3, rates, and scenarios.
* UI includes focus-year selector, KPI cards, charts, projection table with column-group filters, and CSV/XLSX downloads. Show validation errors beside fields; never fail silently.

* [v1.1] The user interface is further specified in section 14 (branding and header, Client details page, tooltips, scenario sliders, mortality-table list). Where section 14 and the bullets above differ, section 14 applies.

## 8. Projection dictionary — LIVE from Model Spec
Translate the listed Excel formulas into Python in the phase order above. A blank year-2 formula means the year-1 formula spills as a dynamic array.
### 8.1 Opening balances and summary
| Cell | Label | Excel formula/value | Meaning |
|---|---|---|---|
| C1 | Act Assets | =X7+AK7+BW7 | PV of SSI + NII assets + NPV of total assets. |
| C2 | Act Liabilities | =P7 | PV expense reserve at start. |
| C3 | Surplus | =C1-C2 | Named proj_surplus. |
| F2 | Assets | =AT5+AU5+AY5+BI5+BJ5+BK5+BL5+BM5+BN5 | Opening balances total. |
| F3 | Liabilities | =AQ4+BP5 | PV tax (AQ4 = SUM(AQ7:AQ70)) + mortgage balance. |
| AC5:AD5 | Salary / supp salary | =salary / =sup_salary | Opening incomes. |
| AT5 | Pre 401k | =pre_401k | Opening balance. |
| AU5 | P Trad IRA | =(pre_IRA) | Opening balance. |
| AY5 | S Trad IRA | =s_pre_IRA | Opening balance. |
| BI5 | Post 401k | =post_401k | Opening balance. |
| BJ5 | Roth IRA | =roth_IRA | Opening balance. |
| BK5 | Sleeve 3 | =Main!B55 | Opening balance. |
| BL5 | Cash backdrop | =cash_cushion_amt | Opening balance. |
| BM5 | Taxable accounts | =+(brokerage+life_ins)-BK5-BL5 | Brokerage less amounts allocated to Sleeve 3 and cash. |
| BN5 | Real assets | =real_estate+other_PMs | Opening balance. |
| BP5 | Mortgage | =mortgage | Opening mortgage balance. |
| BQ5 | Mortgage payment | =-PMT(mort_rate/12,mort_payments,mortgage,0) | Monthly payment. |
| BV5 | Total assets | =AT5+...+BN5 | Opening total assets. |
| BD3 | Draw % | 0.06 | Input: share of IRA balance drawn (PreTaxDraw). |
| CG5 | Cash months | 2 | Input: months of expenses held as cash backdrop. |

### 8.2 Annual projection columns
| Col | Header | Group | Year 1 formula | Year 2+ formula | Meaning |
|---|---|---|---|---|---|
| A | Number | Timeline | =PROJYEARS(1,PROJLENGTH(tblMortality[Age],p_dob,s_dob,TODAY())) |  | Projection year counter 1..N (spills from PROJYEARS). Dynamic-array spill from row 7 (single formula). |
| B | Year | Timeline | =PROJYEARS(cur_year,PROJLENGTH(tblMortality[Age],p_dob,s_dob,TODAY())) |  | Calendar year starting at cur_year (Main!B6). Dynamic-array spill from row 7 (single formula). |
| C | Age p | Timeline | =PROJYEARS(AGENEAREST(p_dob,DATE(B7,12,31)),PROJLENGTH(tblMortality[Age],p_dob,s_dob,TODAY())) |  | Primary age (nearest birthday) at 12/31 of each year. Dynamic-array spill from row 7 (single formula). |
| D | Age s | Timeline | =PROJYEARS(AGENEAREST(s_dob,DATE(B7,12,31)),PROJLENGTH(tblMortality[Age],p_dob,s_dob,TODAY())) |  | Spouse age (nearest birthday) at 12/31. Dynamic-array spill from row 7 (single formula). |
| E | Inflation | Expense inflation | =(INDEX(tblInflation,0,MATCH(InflationScenario,tblInflation[#Headers],0))/100+InflationLoad+1) |  | Annual expense inflation factor = scenario CPI/100 + inflation load + 1 (spills). Dynamic-array spill from row 7 (single formula). |
| F | Inflation | Expense inflation | =E7 | =E8*F7 | Cumulative inflation factor. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| G | Expenses | Expenses | =TimeFactor(t_expenses)*net_expenses*E7 | =IF(E8<>"",G7*E8,"") | Variable (living) expenses = annualized net_expenses x inflation; year 1 = base x E7. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| H | Expenses | Expenses | =BQ7 | =BQ8 | Fixed expenses = mortgage payments (BQ). Rows 8-70 consistent. |
| I | Suvivorship | Survivorship | =PROJECTMORTALITY_RP(tblMortality[#All], PROJLENGTH(tblMortality[Age],p_dob,s_dob,TODAY()), "last_survivor", joint, mort_table) |  | Joint last-survivor survival probability (PROJECTMORTALITY_RP, spills). Dynamic-array spill from row 7 (single formula). |
| J | Discount | Survivorship | =IF(A7<>"",discount_rate^A7,"") | =IF(A8<>"",discount_rate^A8,"") | Discount factor = discount_rate ^ year number. Rows 8-70 consistent. |
| K | Annuity Factor | Survivorship | =MAX(I7*J7,0.00000001) | =IF(J8<>"",I8*J8,"") | Annuity factor = survivorship x discount (floored at 1E-8). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| L | Mid Year Discount | Lifetime expenses | =XLOOKUP(A7,tblDiscountRates[Year],tblDiscountRates[ExpDiscFact]) | =XLOOKUP(A8,tblDiscountRates[Year],tblDiscountRates[ExpDiscFact]) | Mid-year expense discount factor (Discounting!ExpDiscFact). Rows 8-70 consistent. |
| M | Mid Year Mort | Lifetime expenses | =SQRT(I7) | =SQRT(I8*I7) | Mid-year survivorship = SQRT of consecutive survivorship values. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| N | Annuity End Year | Lifetime expenses | =TREASURYDISC(A7,tblDiscountRates[Year],tblDiscountRates[ExpenseDiscountRt])*$I7 | =TREASURYDISC(A8,tblDiscountRates[Year],tblDiscountRates[ExpenseDiscountRt])*$I8 | End-year annuity factor = Treasury-based discount x survivorship. Rows 8-70 consistent. |
| O | PV Expense Flow | Lifetime expenses | =IF(A7<>"",L7*(G7)*M7,"") | =IF(A8<>"",L8*(G8)*M8,"") | PV of year's variable expenses = L x G x M. Rows 8-70 consistent. |
| P | PV Expense Reserve | Lifetime expenses | =IF(A7<>"",SUM(O7:$O$70),"") | =IF(OR(A8="",N7=0),0,SUM(O8:$O$70)/(N7)) | PV expense reserve (liability): sum of remaining PV expenses, divided by prior-year annuity factor N. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| Q | US COLA | SSI | =(INDEX(tblInflation,0,MATCH(COLAScenario,tblInflation[#Headers],0))/100+1) |  | US COLA factor per year from COLAScenario (spills). Dynamic-array spill from row 7 (single formula). |
| R | Cum COLA | SSI | =Q7 | =R7*Q8 | Cumulative COLA factor (also used to inflate tax brackets). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| S | Mid Year Discount | SSI | =XLOOKUP(A7,tblDiscountRates[Year],tblDiscountRates[SSIDiscFact]) | =XLOOKUP(A8,tblDiscountRates[Year],tblDiscountRates[SSIDiscFact]) | Mid-year SSI discount factor. Rows 8-70 consistent. |
| T | Mid Year Mort | SSI | =SQRT($I7) | =SQRT($I8*$I7) | Mid-year survivorship for SSI. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| U | Annuity End Year | SSI | =TREASURYDISC(A7,tblDiscountRates[Year],tblDiscountRates[SSIDiscountRt])*$I7 | =TREASURYDISC(A8,tblDiscountRates[Year],tblDiscountRates[SSIDiscountRt])*$I8 | End-year annuity factor for SSI. Rows 8-70 consistent. |
| V | Forecast SSI | SSI | =FORECASTSSI(C7:C70, Q7:Q70, SSI_ret_age, SSI_PIA, t_SSI_PIA) |  | Forecast annual SSI benefit (FORECASTSSI, spills). Dynamic-array spill from row 7 (single formula). |
| W | PV SSI Payments | SSI | =IF(A7<>"",V7*S7*T7,"") | =IF(A8<>"",V8*S8*T8,"") | PV SSI payment = V x S x T. Rows 8-70 consistent. |
| X | PV SSI Asset | SSI | =IF(A7<>"",SUM(W7:W$70),"") | =IF(OR(A8="",U7=0),0,SUM(W8:W$70)/(U7)) | PV SSI asset: remaining PV payments / prior-year U. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| Y | SSI Shortfall | SSI | =IF(A7<>"",X7-P7,"") | =IF(A8<>"",X8-P8,"") | SSI shortfall = SSI asset - expense reserve (X - P). Rows 8-70 consistent. |
| Z | Mid Year Discount | Future salary | =XLOOKUP(A7,tblDiscountRates[Year],tblDiscountRates[EmpDiscFact]) | =XLOOKUP(A8,tblDiscountRates[Year],tblDiscountRates[EmpDiscFact]) | Mid-year employment discount factor. Rows 8-70 consistent. |
| AA | Mid Year Mort | Future salary | =SQRT($I7) | =SQRT($I8*$I7) | Mid-year survivorship for employment income. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AB | Annuity End Year | Future salary | =TREASURYDISC(A7,tblDiscountRates[Year],tblDiscountRates[EmploymentDiscountRt])*$I7 | =TREASURYDISC(A8,tblDiscountRates[Year],tblDiscountRates[EmploymentDiscountRt])*$I8 | End-year annuity factor for employment income. Rows 8-70 consistent. |
| AC | Salary & Inc | Future salary | =IF(AG7>0,TimeFactor(t_salary)*salary*AG7,TimeFactor(t_income)*net_income)*SQRT(Q7) | =IF(AG8>0,AC7*AG8,TimeFactor(t_income)*net_income)*SQRT(Q8) | Salary / post-retirement income: salary x fraction worked (AG) before retirement, then net_income; grown by SQRT(COLA). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AD | Sup Income | Future salary | =TimeFactor(t_sup_salary)*sup_salary*SQRT(Q7) | =AD7*SQRT(Q8) | Supplemental salary income, grown by SQRT(COLA). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AE | PV Future Salary | Future salary | =IF(A7<>"",(AC7+AD7)*AA7*Z7,"") | =IF(A8<>"",(AC8+AD8)*AA8*Z8,"") | PV of salary + supplemental income. Rows 8-70 consistent. |
| AF | PV Salary Asset | Future salary | =IF(A7<>"",SUM($AE7:AE$70),"") | =IF(OR(A8="",AB7=0),0,SUM($AE8:AE$70)/(AB7)) | PV salary asset (remaining PV / prior-year AB). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AG | Salary Incurred | Future salary | =WORKINCUR(B7,t_ret_date) | =WORKINCUR(B8,t_ret_date) | Fraction of year worked (WORKINCUR with t_ret_date). Rows 8-70 consistent. |
| AI | Inv Income | Investment income | =IF(A7<>"",BK5*((sleeve3_ror)),"") | =IF(A8<>"",BK7*((sleeve3_ror)),"") | Sleeve 3 investment income = prior balance x sleeve3_ror. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AJ | PV Other Income | Investment income | =IF(A7<>"",AI7*S7*T7,"") | =IF(A8<>"",AI8*S8*T8,"") | PV of other income = AI x S x T (same pattern in every row). Rows 7-70 consistent. |
| AK | PV NII | Investment income | =IF(A7<>"",SUM(AJ7:$AJ$70),"") | =IF(OR(A8="",U7=0),0,(SUM(AJ8:$AJ$70)/K7)) | PV NII asset (remaining PV income). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AM | AGI | Tax | =AC7+AD7+AI7+AX7+BB7+V7 | =AC8+AD8+AI8+AX8+BB8+V8 | Taxable AGI = AC+AD+AI+AX+BB+V (income + RMDs + SSI). Rows 8-70 consistent. |
| AN | IRA WD Headroom | Tax | =IraFill(AC7+AD7+AX7+BB7+0.2*AI7,0.8*AI7,joint,R7-1,1,AU5+AY5,1) | =IraFill(AC8+AD8+AX8+BB8+0.2*AI8,0.8*AI8,joint,R8-1,1,AU7+AY7,1) | IRA withdrawal headroom via IraFill. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AO | Tax Paid | Tax | =TaxEst(AC7+AD7+0.2*AI7+BD7+BE7+V7,0.8*AI7,joint,R7-1,1) | =TaxEst(AC8+AD8+0.2*AI8+BD8+BE8+V8,0.8*AI8,joint,R8-1,1) | Estimated federal tax (TaxEst). Rows 8-70 consistent. |
| AP | Gross Fed Tax Rt | Tax | =AO7/AM7 | =AO8/AM8 | Effective federal rate = tax / AGI. Rows 8-70 consistent. |
| AQ | PV Tax Payments | Tax | =AO7*N7 | =AO8*N8 | PV of tax = tax x N. Rows 8-70 consistent. |
| AR | PV Tax Liab | Tax | =SUM(AQ7:$AQ$70) | =SUM(AQ8:$AQ$70)/T7 | PV tax liability (remaining PV tax). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AT | Pre 401k | Pre-tax accounts | =AT5*IF(AG7=0,0,(1+growth_rt_401k)) | =AT7*IF(AG8=0,0,(1+growth_rt_401k)) | Pre-retirement 401k balance grown at growth_rt_401k while working (AG<>0); set to 0 once no salary is earned (AG=0), after the rollover to the Trad IRA in AU. Rows 8-70 consistent. Year 1 uses opening balance (AT5). |
| AU | P Trad IRA | Pre-tax accounts | =IF(AG7<>0,AU5*(1+LTRoR)-(BD7+CM7)*(1+LTRoR)^0.5,AU5*(1+LTRoR)-(BD7+CM7)*(1+LTRoR)^0.5+AT5*(1+LTRoR)^(1-AG7)) | =MAX(IF(AG8<>0,AU7*(1+LTRoR)-(BD8+CM8)*(1+LTRoR)^0.5,AU7*(1+LTRoR)-(BD8+CM8)*(1+LTRoR)^0.5+AT7*(1+LTRoR)^(1-AG8)),0) | Primary traditional IRA roll-forward: growth less distributions (BD + CM), plus rollover of 401k in retirement year. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AV | AGE | Pre-tax accounts | =ATTAINEDAGE(p_dob,DATE(B7-1,12,31)) | =AV7+1 | Primary age counter: ATTAINEDAGE at 12/31 of the prior year (B7-1) in year 1, then +1 per row. No longer depends on TODAY(). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AW | P WD Eligible | Pre-tax accounts | =IF(AV7>59,1,0) | =IF(AV8>59,1,0) | Primary withdrawal-eligible flag (age > 59). Rows 8-70 consistent. |
| AX | P RMD | Pre-tax accounts | =RMD(p_dob,B7,Projection!AU5) | =RMD(p_dob,B8,AU7) | Primary RMD on prior-year IRA balance. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AY | S Trad IRA | Pre-tax accounts | =AY5*(1+LTRoR)-BE7 | =AY7*(1+LTRoR)-BE8 | Spouse traditional IRA roll-forward. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| AZ | S AGE | Pre-tax accounts | =ATTAINEDAGE(s_dob,DATE(B7-1,12,31)) | =AZ7+1 | Spouse age counter: ATTAINEDAGE at 12/31 of the prior year (B7-1) in year 1, then +1 per row. No longer depends on TODAY(). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BA | S WD Eligible | Pre-tax accounts | =IF(AZ7>59,1,0) | =IF(AZ8>59,1,0) | Spouse withdrawal-eligible flag. Rows 8-70 consistent. |
| BB | S RMD | Pre-tax accounts | =RMD(s_dob,B7,AY5) | =RMD(s_dob,B8,AY7) | Spouse RMD on prior-year spouse IRA balance, using calendar year B. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BD | P Plan Dist | Pre-tax distributions | =PreTaxDraw(AN7-AX7,AU5,$BD$3,AW7)+AX7 | =PreTaxDraw(AN8-AX8,AU7,$BD$3,AW8)+AX8 | Primary planned IRA distribution = PreTaxDraw(headroom - RMD, balance, BD3 draw %) + RMD. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BE | S Plan Dist | Pre-tax distributions | =PreTaxDraw(AN7-BB7-BD7,AY5,$BD$3,BA7)+BB7 | =PreTaxDraw(AN8-BB8-BD8,AY7,$BD$3,BA8)+BB8 | Spouse planned IRA distribution. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BI | Post 401k | Post-tax assets | =BI5*(1+growth_rt_401k) | =BI7*(1+growth_rt_401k) | Post-tax 401k balance grown at growth_rt_401k. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BJ | Roth IRA | Post-tax assets | =BJ5*(1+LTRoR)+(CF7-CN7)*(1+LTRoR)^0.5 | =BJ7*(1+LTRoR)+(CF8-CN8)*(1+LTRoR)^0.5 | Roth IRA: growth + (contributions CF - distributions CN). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BK | Sleeve 3 | Post-tax assets | =BK5*(1+sup_inc_irr)-CL7*(1+sup_inc_irr)^0.5 | =BK7*(1+sup_inc_irr)-CL8*(1+sup_inc_irr)^0.5 | Sleeve 3 balance grown at sup_inc_irr less distributions CL. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BL | Cash Backdrop | Post-tax assets | =BL5*(1+growth_rt_401k)+(CG7-CJ7)*(1+growth_rt_401k)^0.5 | =BL7*(1+growth_rt_401k)+(CG8-CJ8)*(1+growth_rt_401k)^0.5 | Cash backdrop: growth + (CG - CJ). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BM | Taxable Accounts | Post-tax assets | =MAX(0,BM5*(1+LTRoR)+(CH7-CK7)*(1+LTRoR)^0.5) | =MAX(0,BM7*(1+LTRoR)+(CH8-CK8)*(1+LTRoR)^0.5) | Taxable brokerage: growth + (CH - CK), floored at 0. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BN | Real Assets | Post-tax assets | =+(real_estate+other_PMs)*E7-CO7 | =IF(A8<>"",BN7*E8-CO8,"") | Real assets: inflated by E, less distributions CO. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BP | Mortgage | Mortgage | =MTGBALEOY($BP$5,mort_rate,$BQ$5,A7) | =MTGBALEOY($BP$5,mort_rate,$BQ$5,A8) | Mortgage balance at end of year (MTGBALEOY). Rows 8-70 consistent. |
| BQ | Payments | Mortgage | =IF(BP5>1,BQ5*12,0) | =IF(BP7>1,$BQ$5*12,0) | Annual mortgage payments (monthly payment x 12 while balance > 1). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| BR | Expense Disc | Mortgage | =TREASURYDISC(A7,tblDiscountRates[Year],tblDiscountRates[ExpenseDiscountRt]) | =TREASURYDISC(A8,tblDiscountRates[Year],tblDiscountRates[ExpenseDiscountRt]) | Expense-discount factor (TREASURYDISC). Rows 8-70 consistent. |
| BS | PV Mort PMTS | Mortgage | =TREASURYDISC(A7,tblDiscountRates[Year],tblDiscountRates[ExpenseDiscountRt])*BQ7 | =TREASURYDISC(A8,tblDiscountRates[Year],tblDiscountRates[ExpenseDiscountRt])*BQ8 | PV of mortgage payments. Rows 8-70 consistent. |
| BT | PV Mortgage Liab | Mortgage | =IF(A7<>"",SUM($BS7:BS$70),"") | =IF(A8<>"",SUM($BS8:BS$70),"")/BR7 | PV mortgage liability (remaining PV payments / prior BR). INCONSISTENT: rows 19, 20, 21, 22, 23, 24… differ from row 8 pattern (rows 8-70). Year 1 uses opening balances / different logic. |
| BV | Total Assets | Totals | =AT7+AU7+AY7+BI7+BJ7+BK7+BL7+BM7+BN7 | =AT8+AU8+AY8+BI8+BJ8+BK8+BL8+BM8+BN8 | Total assets (EOY) = AT+AU+AY+BI+BJ+BK+BL+BM+BN. Rows 8-70 consistent. |
| BW | NPV Assets | Totals | =BV7*J7 | =BV8*J8 | NPV of total assets = BV x J. Row 1 C1 = X7+AK7+BW7. Rows 8-70 consistent. |
| BY | AGI | After-tax income | =AC7+AI7+BD7+BE7+V7+AD7 | =AC8+AI8+BD8+BE8+V8+AD8 | Cash income = AC+AI+BD+BE+V+AD (supplemental income AD now included). Rows 7-70 consistent. |
| BZ | Tax | After-tax income | =AO7 | =AO8 | Tax (= AO). Rows 8-70 consistent. |
| CA | After Tax Inc | After-tax income | =BY7-BZ7 | =BY8-BZ8 | After-tax income = BY - BZ. Rows 8-70 consistent. |
| CC | Surplus | Surplus & cash flow | =IF(A7<>"",AK7+X7+AF7-P7,"") | =IF(A8<>"",AK8+X8+AF8-P8,"") | Year surplus = AK + X + AF - P (PV income assets less PV expense reserve). Rows 8-70 consistent. |
| CD | Cash Flow | Surplus & cash flow | =IF(A7<>"",CA7-G7-H7,"") | =IF(A8<>"",CA8-G8-H8,"") | Annual cash flow = after-tax income - variable - fixed expenses. Rows 8-70 consistent. |
| CF | Roth | Contributions | =MAX(MIN(CD7,ROTH_LIMIT(AM7,joint,C7,D7,A7,3%)),0) | =MAX(MIN(CD8,ROTH_LIMIT(AM8,joint,C8,D8,A8,3%)),0) | Roth contribution = MAX(MIN(cash flow, ROTH_LIMIT),0), using same-year AGI (AM). Rows 7-70 consistent. |
| CG | Cash Backdrop | Contributions | =MAX(MIN(CD7-CF7,(G7+H7)*$CG$5/12),0) | =MAX(MIN(CD8-CF8,(G8+H8)*$CG$5/12),0) | Cash backdrop top-up up to CG5 months of expenses. Rows 8-70 consistent. |
| CH | Brokerage | Contributions | =MAX(CD7-CF7-CG7,0) | =MAX(CD8-CF8-CG8,0) | Remaining surplus into brokerage. Rows 8-70 consistent. |
| CJ | Cash Backdrop | Distributions | =MIN(-MIN(0,CD7),BL5) | =MIN(-MIN(0,CD8),BL7) | Shortfall funding waterfall step 1: cash backdrop. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| CK | Brokerage | Distributions | =MIN(MAX(0,-(CD7+CJ7)),BM5) | =MIN(MAX(0,-(CD8+CJ8)),BM7) | Step 2: brokerage. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| CL | Sleeve 3 | Distributions | =MIN(MAX(-(CJ7+CK7+CD7),0),BK5) | =MIN(MAX(-(CJ8+CK8+CD8),0),BK7) | Step 3: Sleeve 3. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| CM | Trad IRA | Distributions | =MIN(MAX(-(CJ7+CK7+CD7+CL7),0),AU5+AY5) | =MIN(MAX(-(CJ8+CK8+CD8+CL8),0),AU7+AY7) | Step 4: traditional IRA (primary + spouse). Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| CN | Roth | Distributions | =MIN(MAX(-(CJ7+CK7+CD7+CM7+CL7),0),BJ5) | =MIN(MAX(-(CJ8+CK8+CD8+CM8+CL8),0),BJ7) | Step 5: Roth IRA. Rows 8-70 consistent. |
| CO | Real Assets | Distributions | =MIN(MAX(-(CJ7+CK7+CD7+CM7+CL7+CN7),0),BN5) | =MIN(MAX(-(CJ8+CK8+CD8+CM8+CL8+CN8),0),BN7) | Step 6: real assets. Rows 8-70 consistent. Year 1 uses opening balances / different logic. |
| CQ | Total Distributions | Distributions | =SUM(CJ7:CO7) | =SUM(CJ8:CO8) | Total distributions = SUM(CJ:CO). Rows 8-70 consistent. |
| CR | PV Distributions | Distributions | =CQ7*L7 | =CQ8*L8 | PV of distributions = CQ x L. Rows 8-70 consistent. |
| CW | Year | Dashboard feed | =IF(A7<>"",B7,0) | =IF(A8<>"",B8,0) | Year (0 where no projection row). Rows 8-58 consistent. |
| CX | Net Cash Flow | Dashboard feed | =IF(A7<>"",CD7,0) | =IF(A8<>"",CD8,0) | Net cash flow (= CD). Rows 8-58 consistent. |
| CY | SSI Assets | Dashboard feed | =IF(A7<>"",X7,0) | =IF(A8<>"",X8,0) | SSI asset PV (= X). Rows 8-58 consistent. |
| CZ | NII PV | Dashboard feed | =IF(A7<>"",AK7,0) | =IF(A8<>"",AK8,0) | NII PV (= AK). Rows 8-58 consistent. |
| DA | Income PV | Dashboard feed | =IF(A7<>"",AF7,0) | =IF(A8<>"",AF8,0) | Salary asset PV (= AF). Rows 8-58 consistent. |
| DB | Pre Tax | Dashboard feed | =AU5+AY5 | =AU7+AY7 | Pre-tax balances opening: prior-row AU+AY. Rows 8-58 consistent. Year 1 uses opening balances / different logic. |
| DC | Post Tax | Dashboard feed | =BJ5+BK5+BL5+BM5+BI5 | =BJ7+BK7+BL7+BM7+BI7 | Post-tax balances opening: BJ+BK+BL+BM+BI prior row. Rows 8-58 consistent. Year 1 uses opening balances / different logic. |
| DD | Real Assets | Dashboard feed | =BN5 | =BN7 | Real assets prior row (BN). Rows 8-58 consistent. Year 1 uses opening balances / different logic. |
| DE | LT Debt | Dashboard feed | =BT7 | =BT8 | Long-term debt PV (BT). Rows 8-58 consistent. |
| DF | SOL Liability | Dashboard feed | =IF(A7<>"",P7,0) | =IF(A8<>"",P8,0) | Expense liability (= P). Rows 8-58 consistent. |
| DG | Expense Liabilities | Dashboard feed | =DE7+DF7 | =DE8+DF8 | Total liabilities = DE + DF. Rows 8-58 consistent. |
| DH | Total Assets | Dashboard feed | =IF(CW7<>"",CY7+DA7+DB7+DC7+DD7,0) | =IF(CW8<>"",CY8+DA8+DB8+DC8+DD8,0) | Total assets for dashboard = CY+DA+DB+DC+DD. Rows 8-58 consistent. |
| DI | PV Expenses | Dashboard feed | =BS7+O7 | =BS8+O8 | PV expenses = BS + O. Rows 8-58 consistent. |
| DJ | PV Income | Dashboard feed | =AE7+AJ7-AQ7+CR7 | =AE8+AJ8-AQ8+CR8 | PV income = AE+AJ-AQ+CR. Rows 8-58 consistent. |

## 9. Named LAMBDA functions — LIVE from Model Spec
Create a snake_case Python function for each item below. LET means local variables; SEQUENCE means numpy.arange; VSTACK/DROP/TAKE mean concatenate/slice; SWITCH and IFS are ordered branches; ISOMITTED is an optional parameter. Preserve Excel array broadcasting.
### AGENEAREST (In use)
* Parameters: dob, as_of_date
* Purpose: Age at nearest birthday as of a date (rounds up when the next birthday is closer than the last one).
* Used in: Main (5 cells); Projection: C, D; called by: PROJECTMORTALITY, PROJECTMORTALITY_RP, PROJLENGTH
* Excel definition: =LAMBDA(dob,as_of_date, LET(last_bday, DATE(YEAR(as_of_date) - (DATE(YEAR(as_of_date), MONTH(dob), DAY(dob)) > as_of_date), MONTH(dob), DAY(dob)), next_bday, EDATE(last_bday, 12), days_since_last, as_of_date - last_bday, days_to_next, next_bday - as_of_date, age_last, DATEDIF(dob, as_of_date, "y"), age_last + IF(days_to_next < days_since_last, 1, 0)))

### ASOFDATE (In use)
* Parameters: (none)
* Purpose: Valuation date: today if status (retired) = "RETIRED", otherwise the target retirement date t_ret_date.
* Used in: Main (3 cells); called by: PROJECTMORTALITY, PROJECTMORTALITY_RP
* Excel definition: =LAMBDA(IF(retired = "RETIRED", TODAY(), t_ret_date))

### ATTAINEDAGE (In use)
* Parameters: dob, as_of_date
* Purpose: Completed years of age (DATEDIF "y") between a DOB and a date.
* Used in: Main (1 cells); Projection: AV, AZ; called by: 
* Excel definition: =LAMBDA(dob,as_of_date, DATEDIF(dob, as_of_date, "y"))

### EXPECTEDLIFE (In use)
* Parameters: age_col, male_col, female_col, gender, age
* Purpose: Life expectancy for one person: sum of the survival curve (TPXCURVE) from the given age, selecting male/female mortality column.
* Used in: Main (2 cells); called by: 
* Excel definition: =LAMBDA(age_col,male_col,female_col,gender,age, LET(g, UPPER(TRIM(gender)), mortality_col, SWITCH(g, "M", male_col, "F", female_col, NA()), proj_duration, MAX(1, MAX(age_col) - age), SUM(TPXCURVE(age_col, mortality_col, age, proj_duration))))

### EXPECTEDLIFE_JOINT (In use)
* Parameters: age_col, male_col, female_col, gender_x, gender_y, age_x, age_y, status
* Purpose: Expected life for a couple: builds both survival curves and sums joint / last-survivor probabilities (FRASIER).
* Used in: Main (1 cells); called by: 
* Excel definition: =LAMBDA(age_col,male_col,female_col,gender_x,gender_y,age_x,age_y,status, LET(gx, UPPER(TRIM(gender_x)), gy, UPPER(TRIM(gender_y)), col_x, SWITCH(gx, "M", male_col, "F", female_col, NA()), col_y, SWITCH(gy, "M", male_col, "F", female_col, NA()), max_age, MAX(age_col), dur, MAX(1, max_age - age_x, max_age - age_y), tpx, TPXCURVE(age_col, col_x, age_x, dur), tpy, TPXCURVE(age_col, col_y, age_y, dur), SUM(FRASIER(tpx, tpy, status))))

### FORECASTSSI (In use)
* Parameters: age_col, cola_col, ssi_ret_age, ssi_pia, ssi_freq
* Purpose: Annual Social Security benefit by projection row: zero before the SSI election age, then PIA (x12 if monthly) grown by cumulative prior-year COLA. Spills one value per age row.
* Used in: Projection: V; called by: 
* Excel definition: =LAMBDA(age_col,cola_col,ssi_ret_age,ssi_pia,ssi_freq, LET(annual_pia, IF(ssi_freq = "Monthly", ssi_pia * 12, ssi_pia), valid_age, ISNUMBER(age_col), eligible, valid_age * (age_col >= ssi_ret_age) = 1, cola_cum, SCAN(1, cola_col, LAMBDA(acc,c, acc * c)), cola_prior, IFERROR(VSTACK(1, DROP(cola_cum, -1)), 1), benefit, IF(eligible, annual_pia * cola_prior, 0), IF(valid_age, benefit, "")))

### FRASIER (In use (via other LAMBDA))
* Parameters: tpx_array, tpy_array, status
* Purpose: Combines two survival arrays: "joint" = px*py; "last survivor" = px+py-px*py.
* Used in: -; called by: EXPECTEDLIFE_JOINT, PROJECTMORTALITY, PROJECTMORTALITY_RP
* Excel definition: =LAMBDA(tpx_array,tpy_array,status, LET(s, LOWER(TRIM(status)), joint, tpx_array * tpy_array, last_survivor, tpx_array + tpy_array - joint, SWITCH(s, "joint", joint, "last", last_survivor, "last_survivor", last_survivor, "last survivor", last_survivor, NA())))

### IraFill (In use)
* Parameters: ord_inc, ltcg_inc, is_joint, cola_rate, yrs_out, ira_bal, target_sel
* Purpose: IRA withdrawal headroom: how much traditional IRA can be drawn before filling the 12% bracket (target_sel=2) or the 0% LTCG band (otherwise), after standard deduction, with brackets inflated by COLA.
* Used in: Projection: AN; called by: 
* Excel definition: =LAMBDA(ord_inc,ltcg_inc,is_joint,cola_rate,yrs_out,ira_bal,target_sel, LET(idx_factor, (1 + cola_rate) ^ yrs_out, std_ded, IF(is_joint, 32200, 16100) * idx_factor, col_num, IF(is_joint, 2, 1), lt_top_0, INDEX(tblLTGCtax[[Single]:[MFJ]], 1, col_num) * idx_factor, br_top_12, INDEX(tblTax[[Single]:[MFJ]], 2, col_num) * idx_factor, room_lt, lt_top_0 + std_ded - ord_inc - ltcg_inc, room_br, br_top_12 + std_ded - ord_inc, room_amt, IF(target_sel = 2, room_br, room_lt), MIN(ira_bal, MAX(0, room_amt))))

### MTGBALEOY (In use)
* Parameters: principal, annual_rate, pmt, year
* Purpose: Mortgage balance at end of year n: amortization formula with monthly rate, floored at 0.
* Used in: Projection: BP; called by: 
* Excel definition: =LAMBDA(principal,annual_rate,pmt,year, LET(r, annual_rate / 12, n, year * 12, bal, IF(r = 0, principal - pmt * n, principal * (1 + r) ^ n - pmt * ((1 + r) ^ n - 1) / r), MAX(0, bal)))

### PreTaxDraw (In use)
* Parameters: budget, balance, draw_pct, is_elig
* Purpose: Pre-tax account draw = eligibility flag x MAX(0, MIN(budget, draw % x balance, balance)).
* Used in: Projection: BD, BE; called by: 
* Excel definition: =LAMBDA(budget,balance,draw_pct,is_elig, is_elig * MAX(0, MIN(budget, draw_pct * balance, balance)))

### PROJECTMORTALITY_RP (In use)
* Parameters: tbl, proj_duration, status, is_joint, prefix
* Purpose: Survivorship curve used in Projection!I. Uses RP-2014 employee (E) rates before retirement and healthy/disabled retiree rates after (TPXCURVE_RP); joint/last-survivor with spouse via FRASIER.
* Used in: Projection: I; called by: 
* Excel definition: =LAMBDA(tbl,proj_duration,status,is_joint,prefix, LET(hdr, TAKE(tbl, 1), data, DROP(tbl, 1), col, LAMBDA(nm, INDEX(data, 0, MATCH(nm, hdr, 0))), age_col, col("Age"), as_of_date, ASOFDATE(), age_x, AGENEAREST(p_dob, as_of_date), age_y, AGENEAREST(s_dob, as_of_date), p_sex, IF(UPPER(TRIM(p_gender)) = "M", "M", "F"), s_sex, IF(p_sex = "M", "F", "M"), yrs_to_ret, MAX(0, ROUND((t_ret_date - as_of_date) / 365.25, 0)), ret_phase, IF(disabled, "D", "H"), tpx, TPXCURVE_RP(age_col, col(prefix & p_sex & "E"), col(prefix & p_sex & ret_phase), age_x, proj_duration, yrs_to_ret), IF(is_joint, FRASIER(tpx, TPXCURVE_RP(age_col, col(prefix & s_sex & "E"), col(prefix & s_sex & "H"), age_y, proj_duration, 0), status), tpx)))

### PROJLENGTH (In use)
* Parameters: age_col, dob_x, dob_y, as_of_date
* Purpose: Number of projection years = max age in mortality table minus the younger spouse age (min 1).
* Used in: Projection: A, B, C, D, I; called by: 
* Excel definition: =LAMBDA(age_col,dob_x,dob_y,as_of_date, MAX(1, MAX(age_col) - MIN(AGENEAREST(dob_x, as_of_date), AGENEAREST(dob_y, as_of_date))))

### PROJYEARS (In use)
* Parameters: start_year, proj_length
* Purpose: Returns a vertical sequence start_year, start_year+1, ... of length proj_length (spills).
* Used in: Projection: A, B, C, D; called by: 
* Excel definition: =LAMBDA(start_year,proj_length, SEQUENCE(proj_length, 1, start_year, 1))

### RETIREAGE (In use)
* Parameters: dob, ret_date
* Purpose: Age at retirement date from DOB and retirement date (#N/A if inputs invalid).
* Used in: Main (1 cells); called by: 
* Excel definition: =LAMBDA(dob,ret_date, IF(OR(NOT(ISNUMBER(dob)), NOT(ISNUMBER(ret_date)), ret_date < dob), NA(), DATEDIF(dob, ret_date, "y")))

### RMD (In use)
* Parameters: DOB, CalcYear, PriorYearEndBalance
* Purpose: Required minimum distribution = prior-year-end balance / IRS Uniform Lifetime factor (tblLURMD); zero before RMD start age (72/73/75 by birth year).
* Used in: Main (1 cells); Projection: AX, BB; called by: 
* Excel definition: =LAMBDA(DOB,CalcYear,PriorYearEndBalance, LET(Age, CalcYear - YEAR(DOB), StartAge, IF(DOB < DATE(1951, 1, 1), 72, IF(DOB < DATE(1960, 1, 1), 73, 75)), Factor, IF(Age >= 120, 2, XLOOKUP(Age, tblLURMD[attained_age], tblLURMD[factor], NA())), IF(OR(NOT(ISNUMBER(DOB)), NOT(ISNUMBER(CalcYear)), NOT(ISNUMBER(PriorYearEndBalance)), PriorYearEndBalance < 0), NA(), IF(Age < StartAge, 0, PriorYearEndBalance / Factor))))

### ROTH_LIMIT (In use)
* Parameters: Income, Joint, p_age, s_age, [yrs], [infl]
* Purpose: Roth IRA contribution limit with catch-up, MAGI phase-out and inflation indexing; limited to earned income; sums primary and spouse if joint.
* Used in: Projection: CF; called by: 
* Excel definition: =LAMBDA(Income,Joint,p_age,s_age,[yrs],[infl], LET(n, IF(ISOMITTED(yrs), 0, yrs), g, IF(ISOMITTED(infl), 0.025, infl), f, (1 + g) ^ n, base, MAX(7500, FLOOR(7500 * f, 500)), cu, MAX(1100, FLOOR(1100 * f, 100)), lo, MAX(IF(Joint, 242000, 153000), FLOOR(IF(Joint, 242000, 153000) * f, 1000)), rng, MAX(IF(Joint, 10000, 15000), FLOOR(IF(Joint, 10000, 15000) * f, 1000)), hi, lo + rng, amt, LAMBDA(age, LET(L, base + IF(age >= 50, cu, 0), IF(Income <= lo, L, IF(Income >= hi, 0, MIN(L, MAX(200, CEILING(L * (hi - Income) / rng, 10))))))), tot, IF(Joint, amt(p_age) + amt(s_age), amt(p_age)), MIN(tot, MAX(Income, 0))))

### SLEEVEFEE (In use)
* Parameters: Sleeve, AUM
* Purpose: Tiered advisory fee for a sleeve (1-5) on assets under management, tiers at $500k / $2M.
* Used in: Main (5 cells); called by: 
* Excel definition: =LAMBDA(Sleeve,AUM, LET(Tier1, MIN(AUM, 500000), Tier2, MAX(MIN(AUM, 2000000) - 500000, 0), Tier3, MAX(AUM - 2000000, 0), IF(OR(NOT(ISNUMBER(Sleeve)), NOT(ISNUMBER(AUM)), AUM < 0, MOD(Sleeve, 1) <> 0, Sleeve < 1, Sleeve > 5), NA(), SWITCH(Sleeve, 1, 0, 2, Tier1 * 0.75% + Tier2 * 0.6% + Tier3 * 0.5%, 3, Tier1 * 0.75% + Tier2 * 0.6% + Tier3 * 0.5%, 4, Tier1 * 1.25% + Tier2 * 1.1% + Tier3 * 1%, 5, Tier1 * 1.25% + Tier2 * 1.1% + Tier3 * 1%))))

### SS_AIME (In use)
* Parameters: IndexedEarnings
* Purpose: Average Indexed Monthly Earnings: top 35 indexed earnings years / 420.
* Used in: SSIdata (1 cells); called by: 
* Excel definition: =LAMBDA(IndexedEarnings, ROUNDDOWN(SUM(TAKE(SORT(IndexedEarnings, , -1), 35)) / 420, 0))

### SS_PIA (In use)
* Parameters: AIME, BendPoint1, BendPoint2
* Purpose: Primary Insurance Amount from AIME using bend points (90% / 32% / 15%), rounded down to $0.10.
* Used in: SSIdata (1 cells); called by: 
* Excel definition: =LAMBDA(AIME,BendPoint1,BendPoint2, FLOOR.MATH(ROUND(0.9 * MIN(AIME, BendPoint1) + 0.32 * MAX(MIN(AIME, BendPoint2) - BendPoint1, 0) + 0.15 * MAX(AIME - BendPoint2, 0), 4), 0.1))

### TaxEst (In use)
* Parameters: ord_inc, ltcg_inc, is_joint, cola_rate, yrs_out
* Purpose: Federal tax estimate: ordinary brackets (tblTax) + LTCG 0/15/20% (tblLTGCtax) + 3.8% NIIT, standard deduction and thresholds inflated by COLA^years.
* Used in: Main (1 cells); Projection: AO; called by: 
* Excel definition: =LAMBDA(ord_inc,ltcg_inc,is_joint,cola_rate,yrs_out, LET(idx_factor, (1 + cola_rate) ^ yrs_out, std_ded, IF(is_joint, 32200, 16100) * idx_factor, col_num, IF(is_joint, 2, 1), br_start, VSTACK(0, INDEX(tblTax[[Single]:[MFJ]], 0, col_num) * idx_factor), br_rate, VSTACK(0.1, tblTax[Rate]), br_end, VSTACK(DROP(br_start, 1), 1E+99), total_taxable, MAX(0, ord_inc + ltcg_inc - std_ded), ord_taxable, MIN(total_taxable, MAX(0, ord_inc - std_ded)), gain_taxable, total_taxable - ord_taxable, ord_tax, SUM(br_rate * (ord_taxable > br_start) * (IF(ord_taxable < br_end, ord_taxable, br_end) - br_start)), lt_limits, INDEX(tblLTGCtax[[Single]:[MFJ]], 0, col_num) * idx_factor, lt_top_0, INDEX(lt_limits, 1), lt_top_15, INDEX(lt_limits, 2), gain_at_0, MAX(0, MIN(ord_taxable + gain_taxable, lt_top_0) - ord_taxable), gain_at_15, MAX(0, MIN(ord_taxable + gain_taxable, lt_top_15) - MAX(ord_taxable, lt_top_0)), gain_at_20, gain_taxable - gain_at_0 - gain_at_15, niit_tax, 0.038 * MIN(ltcg_inc, MAX(0, ord_inc + ltcg_inc - IF(is_joint, 250000, 200000))), ord_tax + 0.15 * gain_at_15 + 0.2 * gain_at_20 + niit_tax))

### TimeFactor (In use)
* Parameters: Frequency
* Purpose: Annualizing factor: 12 if frequency = "Monthly", else 1.
* Used in: Projection: G, AC, AD; called by: 
* Excel definition: =LAMBDA(Frequency, IF(Frequency = "Monthly", 12, 1))

### TPXCURVE (In use (via other LAMBDA))
* Parameters: age_column, mortality_column, age, proj_duration
* Purpose: Cumulative survival probabilities (tpx) from an age using a single qx column.
* Used in: -; called by: EXPECTEDLIFE, EXPECTEDLIFE_JOINT, PROJECTMORTALITY
* Excel definition: =LAMBDA(age_column,mortality_column,age,proj_duration, LET(max_age, MAX(age_column), ages_lookup, SEQUENCE(MAX(1, proj_duration), 1, age, 1), qx_lookup, XLOOKUP(ages_lookup, age_column, mortality_column, NA()), px, IF(ages_lookup > max_age, 0, 1 - qx_lookup), SCAN(1, px, LAMBDA(acc,p, acc * p))))

### TPXCURVE_RP (In use (via other LAMBDA))
* Parameters: age_column, emp_col, ret_col, age, proj_duration, years_to_ret
* Purpose: Cumulative survival probabilities using employee qx before retirement and retiree qx afterwards.
* Used in: -; called by: PROJECTMORTALITY, PROJECTMORTALITY_RP
* Excel definition: =LAMBDA(age_column,emp_col,ret_col,age,proj_duration,years_to_ret, LET(max_age, MAX(age_column), idx, SEQUENCE(MAX(1, proj_duration), 1, 0, 1), ages_lookup, age + idx, qx_emp, XLOOKUP(ages_lookup, age_column, emp_col, NA()), qx_ret, XLOOKUP(ages_lookup, age_column, ret_col, NA()), qx, IF(idx < years_to_ret, qx_emp, qx_ret), px, IF(ages_lookup > max_age, 0, 1 - qx), SCAN(1, px, LAMBDA(acc,p, acc * p))))

### TREASURYDISC (In use)
* Parameters: t, yrs, rates, [timing]
* Purpose: Discount factor 1/(1+r)^t where r is linearly interpolated from a rate curve; optional timing EOY (default), MID or BOY.
* Used in: Projection: N, U, AB, BR, BS; Discounting (192 cells); Calc (64 cells); called by: 
* Excel definition: =LAMBDA(t,yrs,rates,[timing], LET(tm, IF(ISOMITTED(timing), "EOY", UPPER(timing)), adjT, SWITCH(tm, "MID", MAX(0, t - 0.5), "MIDYEAR", MAX(0, t - 0.5), "BOY", MAX(0, t - 1), t), r, FORECAST.LINEAR(adjT, rates, yrs), 1 / (1 + r) ^ adjT))

### TREASURYRATE (In use)
* Parameters: t
* Purpose: Interpolated spot rate from TreasuryCurve table (FORECAST.LINEAR).
* Used in: Discounting (64 cells); called by: 
* Excel definition: =LAMBDA(t, LET(yrs, TreasuryCurve[Year], rates, TreasuryCurve[Spot Rate], r, FORECAST.LINEAR(t, rates, yrs), r))

### WORKINCUR (In use)
* Parameters: yr, retire_date
* Purpose: Fraction of a calendar year worked before retirement date (0 to 1).
* Used in: Projection: AG; called by: 
* Excel definition: =LAMBDA(yr,retire_date, MEDIAN(0, 1, (retire_date - DATE(yr, 1, 1)) / (DATE(yr + 1, 1, 1) - DATE(yr, 1, 1))))

## 10. Known issues and accepted decisions — LIVE from Model Spec
For open/partly resolved items, match the current Excel formulas for parity, isolate each quirk in one documented location, and expose a legacy_quirks=True configuration where practical.
* #1 Projection!BB: [Resolved] Spouse RMD passes Age p — Resolved: BB now uses RMD(s_dob, B7, AY5), i.e. the calendar year (B), in every row.
* #2 Projection!CN7: [Resolved] Row 7 references header cell — Resolved: CN7 now caps on BJ5 (opening Roth balance); CN8+ use the prior-row balance.
* #3 Projection!AK: [Partly resolved] Year-1 discounting differs — Partly resolved: AJ is fixed: AJ7:AJ70 all = AI*S*T. Still open: AK7 = SUM(AJ7:AJ70) with no divisor, while AK8+ divide by K7 and test U7=0 rather than K7.
* #4 Projection!AM vs BY: [Partly resolved] Two AGI definitions — Partly resolved: BY now includes AD (BY = AC+AI+BD+BE+V+AD). Remaining difference: AM adds RMDs (AX+BB) while BY adds planned IRA distributions (BD+BE).
* #5 Projection!CF: [Resolved] Lagged AGI — Resolved: CF8+ now use same-year AGI (AM of the same row), consistent with CF7.
* #6 Projection!AV, AZ: [Resolved] Age counters use TODAY() — Resolved: AV7 = ATTAINEDAGE(p_dob,DATE(B7-1,12,31)) and AZ7 likewise for the spouse, so they no longer change with the calendar. Note: the PROJLENGTH calls in A:D and I still pass TODAY().
* #7 Projection!BT7:BT70: [Partly resolved] Row pattern breaks — Partly resolved: AT7 now follows the AT8:AT70 pattern. Still open: BT7 has no divisor, BT8:BT18 divide by the prior-row BR, and BT19:BT70 do not.
* #8 Projection!C1 vs CC: [Design decision] Different surplus definitions — Accepted design decision: Projection!C3 (proj_surplus = X7+AK7+BW7-P7) is the PV-based dashboard surplus, while CC (AK+X+AF-P, includes the salary asset and excludes account balances) is a separate year-by-year view. The two intentionally use different bases; interpret each in its own context. No action required.
* #9 Names: [Partly resolved] Broken names — Partly resolved: gl_scores (#REF!) has been deleted. Still open: ChartData (invalid spill reference Projection!CX6#:DF7#) remains broken and is a candidate for deletion. Note gl_score (Main!B72) is a separate, valid name and still exists.
* #10 Names: [Partly resolved] Unreferenced names — Partly resolved: FORECASTSSIOLD and PROJECTMORTALITY_old have been removed. Still present and flagged "Not referenced" in sections 4 and 6 (remove or keep as documented legacy): RMDOLD, GLRiskToleranceLevel, PROJECTMORTALITY and the TPXCURVE chain (TPXCURVE, TPXCURVE_RP, FRASIER).
* #11 LAMBDAs: [Design decision] Hard-coded tax constants — Accepted design decision: TaxEst, IraFill, ROTH_LIMIT and SLEEVEFEE intentionally embed standard deductions ($16,100 / $32,200), NIIT thresholds ($200,000 / $250,000), Roth limits and phase-outs, and fee tiers. Update the LAMBDA definitions when the annual figures change; no action required.
* #12 Main: [Partly resolved] Formula errors — Partly resolved: the Main!M7:N7 and M12:N12 #N/A errors are cleared (now returning fees and fee %), and Main!A63 and Calc!B2:B9 now display the Treasury names (linked data type cells). Still open: Calc!G2:G65 shows #VALUE! because each cell calls TREASURYDISC with a single argument (=TREASURYDISC(F2)) instead of t, yrs, rates.
* #13 Main!B64: [Design decision] discount_rate stores a factor — Accepted design decision: discount_rate (Main!B64, = 1/(1+hurdle_rate) = 0.952) intentionally stores a discount factor, applied as discount_rate^year in Projection!J. The name is kept as is; no action required.
* #14 Projection: [Resolved] Hard-coded year-1 SSI flag — Resolved: the V2 flag has been removed (Projection!V2 is now blank).
* #15 InflationLoad default: [Open] Section 3 and the model default are 0.025, but the repository parity fixtures expect 0.0125, which makes inputs read from the workbook differ from the model defaults and shifts every phase 2 to 6 parity test (for example the headline reserve). Decide the authoritative value, then align the model default, the workbook and the regenerated fixtures. [v1.1]
* #16 IAM2012 mortality: [Partly resolved] The column helper exists and handles single-column tables, but project_mortality_rp must still be changed to call it before IAM2012 can be offered. IAM2012 is therefore withheld from the dropdown. [v1.1]
* #17 Acceptance values and fixtures: [Open] Section 11 values are dated 2026-11-06; fixtures used by the repository tests come from an earlier export. Regenerate both from one workbook state and one as_of_date before using them as release gates. The report test that expects the placeholder firm name "Acme Advisors" must be updated to the branded name. [v1.1]

## 11. Acceptance tests — LIVE workbook reference values
Reference as-of date: 2026-11-06
Run Python with that as_of_date and the defaults in section 3. Tolerance: relative 1e-6 and absolute 0.01 for currency. Re-export this section if the date or workbook inputs change.
### 11.1 Summary
[v1.1] Parity with these values depends on known issues #15 and #17 being resolved.

* Projection!C1 Act Assets = 2806864.9333032
* Projection!C2 Act Liabilities = 3348499.44395255
* Projection!C3 Surplus = -541634.51064935
* Funding ratio = 0.83824560233165
* Projection!F2 assets = 1197000; Projection!F3 liabilities = 224931.207146984
* Projection years = 64
* Peak assets = 10786156.9700746
* Lowest assets where year>0 = 2598458.22134919
### 11.2 First five projection years
| Year | A | Survivorship I | Reserve P | SSI asset X | PV NII AK | AGI AM | Tax AO | Total assets BV | Cash flow CD |
|---|---|---|---|---|---|---|---|---|---|
| 2027 | 1 | 0.999966 | 3348499.443953 | 1192622.368039 | 331874.510126 | 145961.858242 | 9813.422989 | 1346486.457895 | 38884.792058 |
| 2028 | 2 | 0.999853 | 3428571.120341 | 1244765.682771 | 319699.052472 | 152839.440671 | 10029.812881 | 1507512.576961 | 41066.504595 |
| 2029 | 3 | 0.999646 | 3510380.97728 | 1300220.678549 | 305617.902375 | 62217.390944 | 0 | 1591837.087806 | -43481.502611 |
| 2030 | 4 | 0.999324 | 3594732.783153 | 1359246.635774 | 289500.112429 | 31496.192 | 0 | 1666750.549749 | -54955.702087 |
| 2031 | 5 | 0.998863 | 3679473.270897 | 1422131.52587 | 271208.147788 | 32756.03968 | 0 | 1765399.821777 | -59450.100645 |
### 11.3 Helper-function vectors
* RETIREAGE = 60
* EXPECTEDLIFE primary = 26.0409322674023; spouse = 29.9313900584858; joint = 33.7748387510637
* RMD = 0
* TaxEst = 8665.6
* SLEEVEFEE results = 0, 1500, 750, 1875, 1875; total = 6000
* SS_AIME = 12416; SS_PIA = 3925.6
* Add unit tests for AGENEAREST, WORKINCUR, MTGBALEOY, ROTH_LIMIT, IRAFILL, PRETAXDRAW, FRASIER and FORECASTSSI, including edge cases documented in their definitions.

## 12. Deliverables and definition of done
* [v1.1] Additional tests for the application layer: header and title HTML (product name, empty-name prompt, sticky CSS, asset lookup), mortality options and column helper, scenario overrides including the Disposable income slider, and the tooltip dictionary (every input has a tooltip).
* Complete source tree, requirements.txt, README, sample input JSON/YAML, data CSVs, and a repeatable workbook-export script.
* pytest coverage for every helper function and all section 11 values; all tests pass.
* Comparison script reading cached workbook values and reporting max absolute/relative difference for every Projection column.
* Docstrings citing each Excel sheet/column or LAMBDA source; assumptions and open questions documented.
* CLI and Streamlit outputs include downloadable projection CSV/XLSX, summary JSON, and both dashboard charts.

## 13. Export and maintenance notes
* [v1.1] Section 14 and the items marked [v1.1] are not produced by the workbook export. Copy them forward when regenerating this document.
* Preferred handoff: upload this .xlsx workbook to Perplexity and point it to the Python App Spec sheet. Alternatively, copy column A into a UTF-8 .md or .txt file.
* Avoid CSV export for this document because cells containing quotes may be doubled or wrapped.
* Live references depend on TODAY(). Model Spec row references are fixed; regenerate this sheet if rows are inserted/deleted in Model Spec.
* Outstanding/partly resolved areas remain documented in section 10, including the current Calc!G2:G65 TREASURYDISC one-argument errors.
* The FORECAST.LINEAR regression-versus-interpolation distinction is mandatory and called out in section 2.1.

## 14. Application layer amendments — version 1.1
These requirements describe the Streamlit application built on the engine. They do not change any calculation.

### 14.1 Product identity and branding
* Product name: "Fifth Generation Retirement Illustrator". Firm line: "Fifth Generation Advisers · Registered Investment Adviser".
* Palette: navy #1a2744, bronze #c49a4a, off-white #f7f4ef, charcoal #2c2c2c. Typefaces: Playfair Display for headings, Source Sans 3 for body text. Bronze is an accent only (rules, borders, icon highlights).
* Browser tab: page title is the product name; icon is the navy shield (assets/brand/favicon.png).
* Logo files are looked up in assets/brand/ as .svg, then .png, then .jpg. Names: shield_navy, shield_cream, ribbon_navy.
* Header: a navy band running edge to edge, compact, with a 3 px bronze rule below. It holds the shield, the product name, the tagline "Registered Investment Adviser", and the Client details (head icon) and Settings (gear) buttons. It stays fixed below the application top bar while the page scrolls, with an off-white strip beneath it so content cannot show through.
* Title block: a "Prepared for" label above the client name, then the valuation date. When the client name is empty the heading shows the muted placeholder "Add a client name" and no label. Heading anchor icons are hidden.
* Footer on every view: cream shield, the disclosure "Hypothetical illustration based on stated assumptions; not a guarantee of future results.", and the firm line.
* Style-only helper blocks must not add vertical gaps to the page.

### 14.2 Client details page
* Groups: Personal, Income, Expenses, Accounts, Mortgage (client fields). Mortality table, Social Security, Sleeve 3, Rates and Scenarios inputs stay in the sidebar. Client name sits at the top of the page.
* Widgets on this page are keyed cd_<field>. Applying an imported file must, before any widget is drawn, set: the stored client values, the sidebar widget keys, every cd_<field> key, and cd_client_name. Otherwise the widgets' remembered values overwrite the import.
* Client file (JSON): top-level keys are schema, client_name, valuation date and inputs. The default file name is client_inputs.json when no client name is set. Percent fields are stored as fractions and shown as percents.
* Import: the file may be selected or dragged onto the upload box. It is validated and its contents (including the client name) are shown; nothing changes until "Apply imported file" is clicked. Validation errors are shown next to the upload; unknown fields and out-of-range values are rejected.
* If the model cannot run (for example a missing mortality column) the page shows a plain error message and stops; it must not crash.
* Tooltips: every input has an explanatory tooltip (the ? icon), stored in one dictionary. Percent fields add "Enter as a percent, e.g. 3.5 for 3.5%." The wording for Sleeve 3, employment risk spread, inflation load, cash cushion, supplemental salary and post-retirement income is provisional and requires advisor review.

### 14.3 Scenario sliders (what-if)
Sliders never change the client's saved inputs; they apply a temporary copy for the run, and a banner states what is overridden. "Reset sliders" restores all of them.
| Slider | Range | Step | Default | Effect |
|---|---|---|---|---|
| Primary retirement | -60 to +60 months | 1 | 0 | Shifts t_ret_date |
| Spouse retirement (joint only) | -60 to +60 months | 1 | 0 | Shifts t_s_ret_date |
| Advisor rate of return | 0% to 15% (widened to include the client's own rate) | 0.25% | client LTRoR | Overrides LTRoR; asset side only |
| Disposable income [v1.1] | -5% to +25% | 0.5% | 0% | net_expenses x (1 + value) |
Disposable income scales only net_expenses; cash cushion and mortgage payments are unchanged. A positive value means more spending and therefore less cash left over. The slider shows the resulting net expenses beside the client's figure, and the scenario banner reads, for example, "disposable income +10.0% (net expenses $5,500 vs client $5,000)". It combines with the other sliders.

### 14.4 Mortality table list
* The dropdown lists tables found in tblMortality (matched on column prefix, ignoring case and punctuation) from this candidate list: RP-2014 and, when enabled, IAM2012. A value imported from a client file stays selectable so nothing crashes.
* IAM2012 is currently withheld (see known issue #16). If an unavailable table is chosen, the application warns and uses RP-2014.
* tblMortality columns: Age, IAM2012M, IAM2012F, RP-2014ME, RP-2014FE, RP-2014MH, RP-2014FH, RP-2014MD, RP-2014FD. See 5.3 for how columns are chosen.

### 14.5 Deployment and access (planned, not part of acceptance)
* Target host: Streamlit Community Cloud from a GitHub repository. Required: requirements.txt at the repository root, the data CSVs and brand assets committed, .streamlit/config.toml at the root, and the working directory taken to be the repository root. No real client files or secrets may be committed; the repository and app should be private.
* Edited tables saved to data_user/ do not persist on that host.
* Access control options under review: Streamlit native login (OpenID Connect) combined with either a Stripe subscription check (st-paywall) or an allow-list of paid-member emails exported from Substack (a manual snapshot refreshed on a schedule; Substack provides no official subscriber-verification API). Compliance review is required before the tool is offered outside the firm.

### 14.6 Test notes
* Expected updates: the mortality-options tests expect only RP-2014 while IAM2012 is withheld; the dashboard report test must expect the branded firm name rather than "Acme Advisors".
* The workbook parity tests are blocked by known issues #15 and #17.
