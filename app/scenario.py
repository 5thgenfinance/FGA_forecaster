"""What-if slider logic (Streamlit-independent). Sliders never change the client's saved inputs."""
from __future__ import annotations
import calendar
from datetime import date
from pydantic import ValidationError
from model.inputs import ProjectionInputs

SHIFT_MIN, SHIFT_MAX = -60, 60                            # months either side of the client's target date
RETURN_MIN, RETURN_MAX, RETURN_STEP = 0.0, 15.0, 0.25     # percent
SPEND_MIN, SPEND_MAX, SPEND_STEP = -5.0, 25.0, 0.5        # percent change applied to net expenses


def add_months(d: date, n: int) -> date:
    m = d.year * 12 + (d.month - 1) + n
    y, mo = divmod(m, 12)
    return date(y, mo + 1, min(d.day, calendar.monthrange(y, mo + 1)[1]))


def return_bounds(base_pct: float) -> tuple[float, float]:
    """Slider range, widened if the client's own rate lies outside 0-15% so 'no change' stays representable."""
    return min(RETURN_MIN, base_pct), max(RETURN_MAX, base_pct)


def build_overrides(base: ProjectionInputs, shift_p: int = 0, shift_s: int = 0,
                    return_pct: float | None = None, spend_pct: float = 0.0) -> dict:
    """Only values that differ from the client's inputs are returned."""
    o: dict = {}
    if shift_p:
        o["t_ret_date"] = add_months(base.t_ret_date, int(shift_p))
    if shift_s and base.t_s_ret_date is not None:
        o["t_s_ret_date"] = add_months(base.t_s_ret_date, int(shift_s))
    if return_pct is not None and abs(return_pct / 100.0 - base.LTRoR) > 1e-9:
        o["LTRoR"] = return_pct / 100.0
    if spend_pct and abs(spend_pct) > 1e-9:
        o["net_expenses"] = base.net_expenses * (1.0 + spend_pct / 100.0)
    return o


def apply_overrides(base: ProjectionInputs, overrides: dict) -> tuple[ProjectionInputs | None, list[str]]:
    """Return a NEW validated inputs object. The base object is not modified."""
    if not overrides:
        return base, []
    try:
        return ProjectionInputs(**{**base.model_dump(), **overrides}), []
    except ValidationError as e:
        return None, [f"{'.'.join(map(str, x['loc'])) or 'scenario'}: {x['msg']}" for x in e.errors()]


def describe(base: ProjectionInputs, overrides: dict) -> list[str]:
    out = []
    if "t_ret_date" in overrides:
        out.append(f"primary retires {overrides['t_ret_date']:%b %Y} (client: {base.t_ret_date:%b %Y})")
    if "t_s_ret_date" in overrides:
        out.append(f"spouse retires {overrides['t_s_ret_date']:%b %Y} (client: {base.t_s_ret_date:%b %Y})")
    if "LTRoR" in overrides:
        out.append(f"advisor return {overrides['LTRoR'] * 100:.2f}% (client: {base.LTRoR * 100:.2f}%)")
    if "net_expenses" in overrides:
        pct = (overrides["net_expenses"] / base.net_expenses - 1.0) * 100.0 if base.net_expenses else 0.0
        out.append(f"disposable income {pct:+.1f}% (net expenses ${overrides['net_expenses']:,.0f} vs client ${base.net_expenses:,.0f})")
    return out


def warnings(inputs: ProjectionInputs, as_of: date) -> list[str]:
    w = []
    if inputs.retired == "PRERET" and inputs.t_ret_date < as_of:
        w.append("Primary retirement date is before the valuation date while status is PRERET.")
    if inputs.t_s_ret_date is not None and inputs.t_s_ret_date < inputs.p_dob:
        w.append("Spouse retirement date precedes the spouse's birth.")
    return w
