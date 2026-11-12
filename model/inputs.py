"""Validated inputs. Defaults = workbook Main sheet (2026-11-03). Percentages are fractions."""
from __future__ import annotations
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

Freq = Literal["Monthly", "Yearly"]

class ProjectionInputs(BaseModel):
    model_config = {"extra": "forbid"}
    # personal
    primary_dob: date = date(1969, 3, 28)
    spouse_dob: Optional[date] = date(1971, 1, 1)        # None => single
    first_proj_year: int = 2027
    primary_target_ret_date: date = date(2029, 3, 28)
    spouse_target_ret_date: Optional[date] = date(2034, 3, 28)
    ret_status: Literal["PRERET", "RETIRED"] = "PRERET"
    p_gender: Literal["M", "F"] = "M"
    primary_disabled: bool = False
    mortality_table: str = "RP-2014"
    # income / expenses
    salary: float = Field(110_000, ge=0)
    supp_salary: float = Field(0, ge=0)
    income_tax_status: Literal["PRE", "POST"] = "PRE"
    employment_risk_spread: float = 0.015
    post_ret_income: float = Field(0, ge=0)
    net_expenses: float = Field(5_000, ge=0)
    cash_cushion_months: float = 5
    cash_cushion_balance: float = Field(25_000, ge=0)
    inflation_scenario: str = "CPI70"
    inflation_load: float = 0.0125
    cola_scenario: str = "COLA70"
    # accounts
    pretax_401k: float = Field(47_000, ge=0)
    roth_401k: float = Field(0, ge=0)
    primary_trad_ira: float = Field(300_000, ge=0)
    spouse_trad_ira: float = Field(0, ge=0)
    roth_ira: float = Field(150_000, ge=0)
    brokerage: float = Field(300_000, ge=0)
    life_ins: float = Field(0, ge=0)
    real_estate: float = Field(400_000, ge=0)
    other_PMs: float = Field(0, ge=0)
    # mortgage
    mortgage: float = Field(150_000, ge=0)
    mortgage_rate: float = Field(0.03, ge=0, le=0.5)
    mortgage_payments_left: int = Field(60, ge=0)
    # SSI
    ssi_claim_age: int = Field(67, ge=62, le=70)
    ssi_pia: float = Field(3_050, ge=0)
    # sleeve 3
    sleeve3_payment: float = 2_000
    sleeve3_income_rate: float = 0.14
    sleeve3_growth_rate: float = 0.04
    sleeve3_balance: float = Field(200_000, ge=0)   # Main!B55
    # rates
    hurdle_rate: float = Field(0.05, gt=-0.5, lt=1)
    lt_return_rate: float = 0.085
    growth_rate_401k: float = 0.035
    contrib_rate_401k: float = 0.14
    # frequency flags (Main column C)
    expenses_freq: Freq = "Monthly"
    salary_freq: Freq = "Yearly"
    post_ret_income_freq: Freq = "Monthly"
    supp_salary_freq: Freq = "Yearly"
    sleeve3_payment_freq: Freq = "Monthly"
    ssi_pia_freq: Freq = "Monthly"
    cash_cushion_freq: Freq = "Monthly"

    @model_validator(mode="after")
    def _checks(self):
        if self.spouse_dob is not None and not (1900 < self.spouse_dob.year < 2100):
            raise ValueError("Spouse DOB out of range")
        if self.primary_target_ret_date < self.primary_dob:
            raise ValueError("primary retirement date precedes dob")
        return self

    @property
    def joint(self) -> bool:
        return self.spouse_dob is not None

    @property
    def discount_rate(self) -> float:
        """Stored as a FACTOR 1/(1+hurdle), per spec sec. 10 #13."""
        return 1.0 / (1.0 + self.hurdle_rate)

    @property
    def brokerage_net(self) -> float:
        return self.brokerage + self.life_ins
