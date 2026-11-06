"""Streamlit-independent helpers for the input form (unit-testable without Streamlit)."""
from __future__ import annotations
from datetime import date
from typing import Any, get_args, get_origin
from pydantic import ValidationError
from model.inputs import ProjectionInputs

INPUT_GROUPS: dict[str, list[str]] = {
    "Personal": ["p_dob", "p_gender", "disabled", "include_spouse", "s_dob", "mort_table", "retired", "t_ret_date", "t_s_ret_date", "cur_year"],
    "Income": ["salary", "t_salary", "sup_salary", "t_sup_salary", "net_income", "t_income", "inc_tax_status", "spread_emprisk"],
    "Expenses": ["net_expenses", "t_expenses", "cash_cushion", "cash_cushion_amt", "t_cashcush"],
    "Accounts": ["pre_401k", "post_401k", "pre_IRA", "s_pre_IRA", "roth_IRA", "brokerage", "life_ins", "real_estate", "other_PMs"],
    "Mortgage": ["mortgage", "mort_rate", "mort_payments"],
    "Social Security": ["SSI_ret_age", "SSI_PIA", "t_SSI_PIA"],
    "Sleeve 3": ["sleeve3_deployed", "sup_income", "t_sup_income", "sleeve3_ror", "sup_inc_irr"],
    "Rates": ["hurdle_rate", "LTRoR", "growth_rt_401k", "contrib_rt_401k", "InflationLoad"],
    "Scenarios": ["InflationScenario", "COLAScenario"],
}
LABELS = {
    "p_dob": "Primary date of birth", "p_gender": "Primary gender", "disabled": "Primary disabled", "include_spouse": "Include spouse",
    "s_dob": "Spouse date of birth", "mort_table": "Mortality table", "retired": "Retirement status", "t_ret_date": "Primary target retirement date",
    "t_s_ret_date": "Spouse target retirement date", "cur_year": "First projection year", "salary": "Salary", "t_salary": "Salary frequency",
    "sup_salary": "Supplemental salary", "t_sup_salary": "Supplemental salary frequency", "net_income": "Post-retirement income",
    "t_income": "Post-retirement income frequency", "inc_tax_status": "Income tax status", "spread_emprisk": "Employment risk spread (%)",
    "net_expenses": "Net expenses", "t_expenses": "Expense frequency", "cash_cushion": "Cash cushion (months)", "cash_cushion_amt": "Cash cushion amount",
    "t_cashcush": "Cash cushion frequency", "pre_401k": "Pre-tax 401(k)", "post_401k": "Post-tax 401(k)", "pre_IRA": "Primary traditional IRA",
    "s_pre_IRA": "Spouse traditional IRA", "roth_IRA": "Roth IRA", "brokerage": "Brokerage accounts", "life_ins": "Life insurance cash value",
    "real_estate": "Real estate", "other_PMs": "Other precious metals / real assets", "mortgage": "Mortgage balance", "mort_rate": "Mortgage rate (%)",
    "mort_payments": "Remaining payments", "SSI_ret_age": "Social Security election age", "SSI_PIA": "Social Security benefit (PIA)",
    "t_SSI_PIA": "Benefit frequency", "sleeve3_deployed": "Sleeve 3 deployed", "sup_income": "Sleeve 3 payment", "t_sup_income": "Sleeve 3 payment frequency",
    "sleeve3_ror": "Sleeve 3 income rate (%)", "sup_inc_irr": "Sleeve 3 growth (%)", "hurdle_rate": "Hurdle rate (%)", "LTRoR": "Long-term asset return (%)",
    "growth_rt_401k": "401(k) / cash growth (%)", "contrib_rt_401k": "401(k) contribution rate (%)", "InflationLoad": "Inflation load (%)",
    "InflationScenario": "Inflation scenario", "COLAScenario": "COLA scenario",
}
PCT_FIELDS = {"spread_emprisk", "mort_rate", "sleeve3_ror", "sup_inc_irr", "hurdle_rate", "LTRoR", "growth_rt_401k", "contrib_rt_401k", "InflationLoad"}
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
    d["include_spouse"] = inputs.s_dob is not None
    return d

def form_to_inputs(values: dict[str, Any]) -> tuple[ProjectionInputs | None, dict[str, str]]:
    """Widget values -> validated model. Returns (inputs, {field: message}); inputs is None when anything is invalid."""
    v = dict(values)
    include_spouse = bool(v.pop("include_spouse", True))
    for f in PCT_FIELDS:
        if f in v and v[f] is not None:
            v[f] = float(v[f]) / 100.0
    if not include_spouse:
        v["s_dob"], v["t_s_ret_date"] = None, None
    try:
        return ProjectionInputs(**v), {}
    except ValidationError as e:
        errs: dict[str, str] = {}
        for err in e.errors():
            f = str(err["loc"][0]) if err["loc"] else "inputs"
            errs.setdefault(f, err["msg"])
        return None, errs
