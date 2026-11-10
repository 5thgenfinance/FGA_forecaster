"""Streamlit-independent helpers for the input form (unit-testable without Streamlit)."""
from __future__ import annotations
from datetime import date
from typing import Any, get_args, get_origin
from pydantic import ValidationError
from model.inputs import ProjectionInputs

INPUT_GROUPS: dict[str, list[str]] = {
    "Personal": ["primary_dob", "p_gender", "primary_disabled", "include_spouse", "spouse_dob", "mortality_table", "ret_status", "primary_target_ret_date", "spouse_target_ret_date", "first_proj_year"],
    "Income": ["salary", "salary_freq", "supp_salary", "supp_salary_freq", "post_ret_income", "post_ret_income_freq", "income_tax_status", "employment_risk_spread"],
    "Expenses": ["net_expenses", "expenses_freq", "cash_cushion_months", "cash_cushion_balance", "cash_cushion_freq"],
    "Accounts": ["pretax_401k", "roth_401k", "primary_trad_ira", "spouse_trad_ira", "roth_ira", "brokerage", "life_ins", "real_estate", "other_PMs"],
    "Mortgage": ["mortgage", "mortgage_rate", "mortgage_payments_left"],
    "Social Security": ["ssi_claim_age", "ssi_pia", "ssi_pia_freq"],
    "Sleeve 3": ["sleeve3_balance", "sleeve3_payment", "sleeve3_payment_freq", "sleeve3_income_rate", "sleeve3_growth_rate"],
    "Rates": ["hurdle_rate", "lt_return_rate", "growth_rate_401k", "contrib_rate_401k", "inflation_load"],
    "Scenarios": ["inflation_scenario", "cola_scenario"],
}
LABELS = {
    "primary_dob": "Primary date of birth", "p_gender": "Primary gender", "primary_disabled": "Primary disabled", "include_spouse": "Include spouse",
    "spouse_dob": "Spouse date of birth", "mortality_table": "Mortality table", "ret_status": "Retirement status", "primary_target_ret_date": "Primary target retirement date",
    "spouse_target_ret_date": "Spouse target retirement date", "first_proj_year": "First projection year", "salary": "Salary", "salary_freq": "Salary frequency",
    "supp_salary": "Supplemental salary", "supp_salary_freq": "Supplemental salary frequency", "post_ret_income": "Post-retirement income",
    "post_ret_income_freq": "Post-retirement income frequency", "income_tax_status": "Income tax status", "employment_risk_spread": "Employment risk spread (%)",
    "net_expenses": "Net expenses", "expenses_freq": "Expense frequency", "cash_cushion_months": "Cash cushion (months)", "cash_cushion_balance": "Cash cushion amount",
    "cash_cushion_freq": "Cash cushion frequency", "pretax_401k": "Pre-tax 401(k)", "roth_401k": "Post-tax 401(k)", "primary_trad_ira": "Primary traditional IRA",
    "spouse_trad_ira": "Spouse traditional IRA", "roth_ira": "Roth IRA", "brokerage": "Brokerage accounts", "life_ins": "Life insurance cash value",
    "real_estate": "Real estate", "other_PMs": "Other precious metals / real assets", "mortgage": "Mortgage balance", "mortgage_rate": "Mortgage rate (%)",
    "mortgage_payments_left": "Remaining payments", "ssi_claim_age": "Social Security election age", "ssi_pia": "Social Security benefit (PIA)",
    "ssi_pia_freq": "Benefit frequency", "sleeve3_balance": "Sleeve 3 deployed", "sleeve3_payment": "Sleeve 3 payment", "sleeve3_payment_freq": "Sleeve 3 payment frequency",
    "sleeve3_income_rate": "Sleeve 3 income rate (%)", "sleeve3_growth_rate": "Sleeve 3 growth (%)", "hurdle_rate": "Hurdle rate (%)", "lt_return_rate": "Long-term asset return (%)",
    "growth_rate_401k": "401(k) / cash growth (%)", "contrib_rate_401k": "401(k) contribution rate (%)", "inflation_load": "Inflation load (%)",
    "inflation_scenario": "Inflation scenario", "cola_scenario": "COLA scenario",
}
PCT_FIELDS = {"employment_risk_spread", "mortgage_rate", "sleeve3_income_rate", "sleeve3_growth_rate", "hurdle_rate", "lt_return_rate", "growth_rate_401k", "contrib_rate_401k", "inflation_load"}
from app.help_text import HELP

def field_kind(name: str) -> str:
    """'bool' | 'date' | 'int' | 'float' | 'choice' | 'text' for a ProjectionInputs field."""
    if name == "include_spouse": return "bool"
    ann = ProjectionInputs.model_fields[name].annotation
    if get_origin(ann) is not None and type(None) in get_args(ann):
        ann = next(a for a in get_args(ann) if a is not type(None))
    if get_origin(ann) is not None and ann.__class__.__name__ != "type":
        return "choice" if str(get_origin(ann)).endswith("Literal") else "text"
    return {bool: "bool", date: "date", int: "int", float: "float", str: "text"}.get(ann, "text")

def choices(name: str) -> list:
    ann = ProjectionInputs.model_fields[name].annotation
    return list(get_args(ann))

def to_form_values(inputs: ProjectionInputs) -> dict[str, Any]:
    """Model -> widget values (fractions shown as percent, spouse flag added)."""
    d = inputs.model_dump()
    for f in PCT_FIELDS:
        d[f] = round(d[f] * 100, 6)
    d["include_spouse"] = inputs.spouse_dob is not None
    return d

def form_to_inputs(values: dict[str, Any]) -> tuple[ProjectionInputs | None, dict[str, str]]:
    """Widget values -> validated model. Returns (inputs, {field: message}); inputs is None when anything is invalid."""
    v = dict(values)
    include_spouse = bool(v.pop("include_spouse", True))
    for f in PCT_FIELDS:
        if f in v and v[f] is not None:
            v[f] = float(v[f]) / 100.0
    if not include_spouse:
        v["spouse_dob"], v["spouse_target_ret_date"] = None, None
    try:
        return ProjectionInputs(**v), {}
    except ValidationError as e:
        errs: dict[str, str] = {}
        for err in e.errors():
            f = str(err["loc"][0]) if err["loc"] else "inputs"
            errs.setdefault(f, err["msg"])
        return None, errs
