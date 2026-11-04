# Decisions and findings

## Phase 2 (vector stage)
- Horizon: `proj_length(max mortality age, younger DOB, as_of_date)`, capped at 64.
- `as_of_date` stands in for TODAY(): sets projection length and, if status is RETIRED, the mortality valuation date.
  When PRERET the valuation date is `t_ret_date` (Excel ASOFDATE).
- Year-1 reserves (P, X, AF, BT) are plain sums; years 2+ divide by the prior-year annuity-end factor.
- BT rows 8-18 divide by prior-row BR, rows 19+ do not (spec issue #7); `legacy_quirks=True` reproduces it.
- Blank RP-2014 qx raises unless `allow_blank_qx=True`.

## Phase 3 (forward loop)
- Forward columns do not depend on the discount curve (only BW uses the flat hurdle factor).
- AI = prior Sleeve 3 balance x sleeve3_ror (income). 401k (AT) rolls into AU in the first year AG = 0.
- Single person: spouse columns AY, BB, BE = 0 and AZ is NaN (Excel would error on a blank spouse DOB).

## Phase 4 (PV columns, dashboard, summary)
- Dashboard feed covers 52 years (Projection rows 7-58); `feed_years=None` extends it to 64.
- AK year t>=2 divides by K[t-1] (flat hurdle discounting) while AJ uses curve-based factors (spec issue #3).
- AR last row is #DIV/0! in Excel and NaN here. New column `UNFUNDED` (not in Excel).

## Phase 5 (parity harness and sweeps)
- Tolerances: spec values (abs 0.01, rel 1e-6) for currency columns; 1e-9 for factor/ratio columns. `--strict` uses abs 1e-6 / rel 1e-9.
- A reference case = inputs.json read from the workbook's defined names + cached Projection values + KPI JSON.
  `--as-of` must be the recalculation date. Sweeps are sanity checks, not parity.
- The workbook round-trip test exports the tables from the same workbook as the reference values; a frozen `data/` snapshot
  stays the baseline (the linked Treasury curve moves whenever Excel refreshes).

## Phase 6 (client visualizations)
- Charts use the full 64-year horizon (`feed_years=None`) trimmed to primary age <= 100 (`chart_age_limit`); KPIs use the full run.
  Excel's 52-year feed would stop before assets are exhausted in the default case (2083, primary age 114).
- DH is labelled "Total resources": it includes the present value of Social Security and future earnings, not just accounts.
- The funding ratio is described to clients as PV resources / PV lifetime spending, not a probability of success.
- Year-by-year charts are nominal dollars and assume both people are alive in every year; the funding ratio is survivorship-weighted.
  That is why a plan can show savings lasting to age 114 and still show an 84% funding ratio.
- Client report never shows dates of birth. The disclosure text is a draft pending compliance review.
- PNG/PDF export is optional (kaleido; Chrome for kaleido >= 1). If unavailable the CLI still writes every other file and exits 4.
- The Streamlit UI was syntax-checked and its form logic is unit-tested (`app/ui_helpers.py`); it has not been run in a live Streamlit session.

## Findings to review (behavior preserved for parity, not endorsed)
1. Shortfall IRA withdrawals (CM) are not in taxable income (AO) or AGI (AM). Brokerage (CK) and Sleeve 3 (CL) withdrawals are untaxed.
2. CM draws from AU+AY combined but is deducted entirely from AU (AU floored at 0 from year 2).
3. AM (RMD-based) and BY (planned-distribution-based) are two AGI definitions (spec issue #4).
4. Hurdle rate changes C1 but not C2 (drives J/K, AK, BW1; the liability P uses the Treasury curve).
5. The mortgage is not in the C2 reserve; removing it raises the funding ratio from 0.84 to 0.97 through the asset side.
6. SSI_PIA is not adjusted for the election age (age 62 -> 1.03, age 70 -> 0.77 with the same PIA).
7. Sleeve 3 pays 14% income and grows 4%; AK1 is about 0.33M, roughly 12% of C1.
8. Last-survivor mortality is applied to full household expenses; there is no expense step-down after the first death.
9. Default return assumptions are aggressive (12.5% long-term assets, 14% Sleeve 3 income, 3.5% on 401k/cash, 2.5% inflation load); review before client use.

## Open
- Single-person and other scenarios are not yet parity-tested against Excel (needs recalculated reference cases).
