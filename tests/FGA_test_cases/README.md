# Case studies

Ten client files in the app's own format (`schema: fga-client-v1`). Open any of them with **Client details -> Import**, or run them through `tests/test_case_studies.py`.
All use the current input names and `RP-2014`, `CPI70`/`COLA70`. The names and people are invented.

| File | Client | What it exercises | Expected direction |
|---|---|---|---|
| 01_smith_baseline_couple | Bryan and Melissa Smith | The reference couple (workbook defaults): joint plan, both still working, mortgage, Sleeve 3 | Baseline for the comparison tests |
| 02_single_preretirement_modest | Dana Reyes | Single person (no spouse fields), 17 years to retirement, small mortgage | Runs; no spouse columns used |
| 03_retired_couple_pension | Walter and Joan Pruitt | `ret_status` RETIRED, both past retirement dates, pension as post-retirement income, SSI already flowing, large IRAs (RMDs) | Runs; salary asset is zero |
| 04_wealthy_overfunded_single | Margaret Lindqvist | Very high assets against modest spending, SSI claimed at 70 | Funding ratio above 100% |
| 05_underfunded_late_saver | Curtis Boone | Late saver with little saved and high spending | Funding ratio below 100% |
| 06_young_family_large_mortgage | Carlos and Elena Alvarez | Long horizon, supplemental salary, 28-year mortgage, life insurance cash value | Runs; mortgage liability present |
| 07_disabled_primary_age_gap | Hollis and Priya Nair | `primary_disabled` true, 10-year age gap, income tax status POST, SSI claimed at 62 | Runs; disabled mortality column used |
| 08_sleeve3_income_portfolio | Eleanor and Tom Whitfield | Large Sleeve 3 balance carved out of brokerage, near-term retirement | Runs; taxable account = brokerage - Sleeve 3 - cash |
| 09_edge_minimal_assets | Test Case Minimal Assets | Edge: every balance zero, no mortgage, no SSI, 37 years to go | Must not crash (zero tax and AGI divisions) |
| 10_edge_very_old_retired_single | Test Case Age 91 | Edge: very short horizon, high mortality, RMDs from age 91 | Must not crash |

## What the tests check

`tests/test_case_studies.py` does not compare against workbook numbers (the golden and parity tests do that). It checks properties that must hold whatever the exact figures are:

1. Every file has the right schema and validates as `ProjectionInputs`.
2. Every file runs end to end and returns finite headline figures.
3. Funding ratio direction for cases 04 (above 1) and 05 (below 1).
4. The same client expressed Monthly or Yearly gives the same result.
5. More spending lowers the funding ratio; more assets or a higher Social Security benefit raises it; a higher long-term return raises it.
6. Running the same case twice gives identical results.

## Adding your own

Save a real-looking client from the app (**Client details -> save**), anonymise it, drop it in this folder, and it is picked up automatically. Never commit real client files.
