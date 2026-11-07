"""Validated inputs. Defaults = workbook Main sheet (2026-11-03). Percentages are fractions."""
from __future__ import annotations
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

Freq = Literal["Monthly", "Yearly"]

class ProjectionInputs(BaseModel):
    model_config = {"extra": "forbid"}
    # personal
    p_dob: date = date(1969, 3, 28)
    s_dob: Optional[date] = date(1971, 1, 1)        # None => single
    cur_year: int = 2027
    t_ret_date: date = date(2029, 3, 28)
    t_s_ret_date: Optional[date] = date(2034, 3, 28)
    retired: Literal["PRERET", "RETIRED"] = "PRERET"
    p_gender: Literal["M", "F"] = "M"
    disabled: bool = False
    mort_table: str = "RP-2014"
    # income / expenses
    salary: float = Field(110_000, ge=0)
    sup_salary: float = Field(0, ge=0)
    inc_tax_status: Literal["PRE", "POST"] = "PRE"
    spread_emprisk: float = 0.015
    net_income: float = Field(0, ge=0)
    net_expenses: float = Field(5_000, ge=0)
    cash_cushion: float = 5
    cash_cushion_amt: float = Field(25_000, ge=0)
    InflationScenario: str = "CPI70"
    InflationLoad: float = 0.025
    COLAScenario: str = "COLA70"
    # accounts
    pre_401k: float = Field(47_000, ge=0)
    post_401k: float = Field(0, ge=0)
    pre_IRA: float = Field(300_000, ge=0)
    s_pre_IRA: float = Field(0, ge=0)
    roth_IRA: float = Field(150_000, ge=0)
    brokerage: float = Field(300_000, ge=0)
    life_ins: float = Field(0, ge=0)
    real_estate: float = Field(400_000, ge=0)
    other_PMs: float = Field(0, ge=0)
    # mortgage
    mortgage: float = Field(150_000, ge=0)
    mort_rate: float = Field(0.03, ge=0, le=0.5)
    mort_payments: int = Field(60, ge=0)
    # SSI
    SSI_ret_age: int = Field(67, ge=62, le=70)
    SSI_PIA: float = Field(3_050, ge=0)
    # sleeve 3
    sup_income: float = 2_000
    sleeve3_ror: float = 0.14
    sup_inc_irr: float = 0.04
    sleeve3_deployed: float = Field(200_000, ge=0)   # Main!B55
    # rates
    hurdle_rate: float = Field(0.05, gt=-0.5, lt=1)
    LTRoR: float = 0.125
    growth_rt_401k: float = 0.035
    contrib_rt_401k: float = 0.14
    # frequency flags (Main column C)
    t_expenses: Freq = "Monthly"
    t_salary: Freq = "Yearly"
    t_income: Freq = "Monthly"
    t_sup_salary: Freq = "Yearly"
    t_sup_income: Freq = "Monthly"
    t_SSI_PIA: Freq = "Monthly"
    t_cashcush: Freq = "Monthly"

    @model_validator(mode="after")
    def _checks(self):
        if self.s_dob is not None and not (1900 < self.s_dob.year < 2100):
            raise ValueError("s_dob out of range")
        if self.t_ret_date < self.p_dob:
            raise ValueError("t_ret_date precedes p_dob")
        return self

    @property
    def joint(self) -> bool:
        return self.s_dob is not None

    @property
    def discount_rate(self) -> float:
        """Stored as a FACTOR 1/(1+hurdle), per spec sec. 10 #13."""
        return 1.0 / (1.0 + self.hurdle_rate)

    @property
    def brokerage_net(self) -> float:
        return self.brokerage + self.life_ins
