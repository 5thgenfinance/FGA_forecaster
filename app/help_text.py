"""Tooltip text for every input (the little ? next to each field). Edit the wording here; nothing else needs to change."""
from __future__ import annotations

_PCT = {"employment_risk_spread", "mortgage_rate", "sleeve3_income_rate", "sleeve3_growth_rate", "hurdle_rate", "lt_return_rate",
        "growth_rate_401k", "contrib_rate_401k", "inflation_load"}
_PCT_HINT = " Enter as a percent, e.g. 3.5 for 3.5%."

_TEXT = {
    # Personal
    "primary_dob": "Primary client's date of birth. Sets current age and the starting point of the mortality curve.",
    "p_gender": "Selects the male or female mortality column. The spouse is assumed to be the opposite sex.",
    "primary_disabled": "Tick if the primary client is disabled. Uses the disabled mortality column where the table has one; tables without it ignore this box.",
    "include_spouse": "Untick for a single-person plan.",
    "spouse_dob": "Spouse's date of birth.",
    "mortality_table": "Mortality table used for survival probabilities.",
    "ret_status": "PRERET: the primary client is still working at the valuation date. RETIRED: already retired.",
    "primary_target_ret_date": "Date the primary client plans to stop working.",
    "spouse_target_ret_date": "Date the spouse plans to stop working.",
    "first_proj_year": "First calendar year of the projection.",
    # Income
    "salary": "Primary client's earned income before retirement, in dollars per the frequency chosen below.",
    "salary_freq": "Whether the salary above is entered per year or per month.",
    "supp_salary": "Additional earned income beyond the salary above, such as the spouse's pay, in dollars per the frequency chosen below.",
    "supp_salary_freq": "Whether the supplemental salary is entered per year or per month.",
    "post_ret_income": "Income expected after retirement other than Social Security (for example a pension), after tax, per the frequency below.",
    "post_ret_income_freq": "Whether post-retirement income is entered per month or per year.",
    "income_tax_status": "Tax status of the income entered (PRE or POST tax).",
    "employment_risk_spread": "Extra discount spread applied to employment income to reflect the risk that it stops early.",
    # Expenses
    "net_expenses": "Household spending the plan must fund, per the frequency below.",
    "expenses_freq": "Whether expenses are entered per month or per year.",
    "cash_cushion_months": "Months of expenses to keep in cash as a reserve.",
    "cash_cushion_balance": "Dollar amount currently held as the cash reserve.",
    "cash_cushion_freq": "Whether the cash cushion amount is entered per month or per year.",
    # Accounts
    "pretax_401k": "Current balance of pre-tax (traditional) 401(k) accounts.",
    "roth_401k": "Current balance of after-tax (Roth) 401(k) accounts.",
    "primary_trad_ira": "Current balance of the primary client's traditional IRA.",
    "spouse_trad_ira": "Current balance of the spouse's traditional IRA.",
    "roth_ira": "Current balance of Roth IRAs.",
    "brokerage": "Current value of taxable brokerage accounts.",
    "life_ins": "Cash surrender value of life insurance (not the death benefit). Counted together with brokerage assets.",
    "real_estate": "Current market value of real estate owned.",
    "other_PMs": "Current value of precious metals and other real assets.",
    # Mortgage
    "mortgage": "Outstanding mortgage principal.",
    "mortgage_rate": "Annual interest rate on the mortgage.",
    "mortgage_payments_left": "Number of monthly mortgage payments remaining.",
    # Social Security
    "ssi_claim_age": "Age at which Social Security benefits are elected (62 to 70).",
    "ssi_pia": "Monthly Primary Insurance Amount from the Social Security statement. Not adjusted for election age: change it when you change the election age.",
    "ssi_pia_freq": "Whether the Social Security benefit is entered per month or per year.",
    # Sleeve 3
    "sleeve3_balance": "Dollars allocated to Sleeve 3.",
    "sleeve3_payment": "Payment received from Sleeve 3, per the frequency below.",
    "sleeve3_payment_freq": "Whether the Sleeve 3 payment is entered per month or per year.",
    "sleeve3_income_rate": "Income rate earned on Sleeve 3.",
    "sleeve3_growth_rate": "Annual growth of the Sleeve 3 payment.",
    # Rates
    "hurdle_rate": "Drives asset-side discounting only; the spending liability uses the Treasury curve.",
    "lt_return_rate": "Long-term expected return on invested assets.",
    "growth_rate_401k": "Annual growth rate applied to 401(k) and cash balances.",
    "contrib_rate_401k": "Share of salary contributed to the 401(k) while working.",
    "inflation_load": "Extra inflation added on top of the selected inflation scenario.",
    # Scenarios
    "inflation_scenario": "Inflation path used to grow expenses.",
    "cola_scenario": "Cost-of-living adjustment path applied to Social Security benefits.",
}

HELP = {k: v + (_PCT_HINT if k in _PCT else "") for k, v in _TEXT.items()}
