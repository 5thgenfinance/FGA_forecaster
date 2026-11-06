"""Tooltip text for every input (the little ? next to each field). Edit the wording here; nothing else needs to change."""
from __future__ import annotations

_PCT = {"spread_emprisk", "mort_rate", "sleeve3_ror", "sup_inc_irr", "hurdle_rate", "LTRoR",
        "growth_rt_401k", "contrib_rt_401k", "InflationLoad"}
_PCT_HINT = " Enter as a percent, e.g. 3.5 for 3.5%."

_TEXT = {
    # Personal
    "p_dob": "Primary client's date of birth. Sets current age and the starting point of the mortality curve.",
    "p_gender": "Selects the male or female mortality column. The spouse is assumed to be the opposite sex.",
    "disabled": "Tick if the primary client is disabled. Uses the disabled mortality column where the table has one; tables without it ignore this box.",
    "include_spouse": "Untick for a single-person plan.",
    "s_dob": "Spouse's date of birth.",
    "mort_table": "Mortality table used for survival probabilities.",
    "retired": "PRERET: the primary client is still working at the valuation date. RETIRED: already retired.",
    "t_ret_date": "Date the primary client plans to stop working.",
    "t_s_ret_date": "Date the spouse plans to stop working.",
    "cur_year": "First calendar year of the projection.",
    # Income
    "salary": "Primary client's earned income before retirement, in dollars per the frequency chosen below.",
    "t_salary": "Whether the salary above is entered per year or per month.",
    "sup_salary": "Additional earned income beyond the salary above, such as the spouse's pay, in dollars per the frequency chosen below.",
    "t_sup_salary": "Whether the supplemental salary is entered per year or per month.",
    "net_income": "Income expected after retirement other than Social Security (for example a pension), after tax, per the frequency below.",
    "t_income": "Whether post-retirement income is entered per month or per year.",
    "inc_tax_status": "Tax status of the income entered (PRE or POST tax).",
    "spread_emprisk": "Extra discount spread applied to employment income to reflect the risk that it stops early.",
    # Expenses
    "net_expenses": "Household spending the plan must fund, per the frequency below.",
    "t_expenses": "Whether expenses are entered per month or per year.",
    "cash_cushion": "Months of expenses to keep in cash as a reserve.",
    "cash_cushion_amt": "Dollar amount currently held as the cash reserve.",
    "t_cashcush": "Whether the cash cushion amount is entered per month or per year.",
    # Accounts
    "pre_401k": "Current balance of pre-tax (traditional) 401(k) accounts.",
    "post_401k": "Current balance of after-tax (Roth) 401(k) accounts.",
    "pre_IRA": "Current balance of the primary client's traditional IRA.",
    "s_pre_IRA": "Current balance of the spouse's traditional IRA.",
    "roth_IRA": "Current balance of Roth IRAs.",
    "brokerage": "Current value of taxable brokerage accounts.",
    "life_ins": "Cash surrender value of life insurance (not the death benefit). Counted together with brokerage assets.",
    "real_estate": "Current market value of real estate owned.",
    "other_PMs": "Current value of precious metals and other real assets.",
    # Mortgage
    "mortgage": "Outstanding mortgage principal.",
    "mort_rate": "Annual interest rate on the mortgage.",
    "mort_payments": "Number of monthly mortgage payments remaining.",
    # Social Security
    "SSI_ret_age": "Age at which Social Security benefits are elected (62 to 70).",
    "SSI_PIA": "Monthly Primary Insurance Amount from the Social Security statement. Not adjusted for election age: change it when you change the election age.",
    "t_SSI_PIA": "Whether the Social Security benefit is entered per month or per year.",
    # Sleeve 3
    "sleeve3_deployed": "Dollars allocated to Sleeve 3.",
    "sup_income": "Payment received from Sleeve 3, per the frequency below.",
    "t_sup_income": "Whether the Sleeve 3 payment is entered per month or per year.",
    "sleeve3_ror": "Income rate earned on Sleeve 3.",
    "sup_inc_irr": "Annual growth of the Sleeve 3 payment.",
    # Rates
    "hurdle_rate": "Drives asset-side discounting only; the spending liability uses the Treasury curve.",
    "LTRoR": "Long-term expected return on invested assets.",
    "growth_rt_401k": "Annual growth rate applied to 401(k) and cash balances.",
    "contrib_rt_401k": "Share of salary contributed to the 401(k) while working.",
    "InflationLoad": "Extra inflation added on top of the selected inflation scenario.",
    # Scenarios
    "InflationScenario": "Inflation path used to grow expenses.",
    "COLAScenario": "Cost-of-living adjustment path applied to Social Security benefits.",
}

HELP = {k: v + (_PCT_HINT if k in _PCT else "") for k, v in _TEXT.items()}
