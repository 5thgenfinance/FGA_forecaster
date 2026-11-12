"""Streamlit rendering of the scenario sliders."""
from __future__ import annotations
from datetime import date
import streamlit as st
from app import scenario as S
from model.inputs import ProjectionInputs


def _reset() -> None:
    st.session_state["sc_reset_n"] = st.session_state.get("sc_reset_n", 0) + 1


def render_scenario(base: ProjectionInputs, as_of: date):
    """Draw the sliders; returns (effective_inputs | None, overrides, messages)."""
    n = st.session_state.setdefault("sc_reset_n", 0)
    with st.expander("Scenario sliders (what-if)", expanded=True):
        sp = st.slider("Primary retirement: months earlier (-) / later (+)", S.SHIFT_MIN, S.SHIFT_MAX, 0, 1,
                       key=f"sc_p_{n}", format="%d mo")
        st.caption(f"Primary retires {S.add_months(base.primary_target_ret_date, sp):%b %Y} (client: {base.primary_target_ret_date:%b %Y})")
        ss = 0
        if base.spouse_target_ret_date is not None:
            ss = st.slider("Spouse retirement: months earlier (-) / later (+)", S.SHIFT_MIN, S.SHIFT_MAX, 0, 1,
                           key=f"sc_s_{n}", format="%d mo")
            st.caption(f"Spouse retires {S.add_months(base.spouse_target_ret_date, ss):%b %Y} (client: {base.spouse_target_ret_date:%b %Y})")
        base_pct = round(base.lt_return_rate * 100, 6)
        lo, hi = S.return_bounds(base_pct)
        rp = st.slider("Advisor rate of return (%)", lo, hi, base_pct, S.RETURN_STEP,
                       key=f"sc_r_{n}_{base_pct}", format="%.2f%%",
                       help="Long-term asset return. Affects the asset side only; the spending liability does not change.")
        dp = st.slider("Disposable income (% change in net expenses)", S.SPEND_MIN, S.SPEND_MAX, 0.0, S.SPEND_STEP,
                       key=f"sc_d_{n}", format="%.1f%%",
                       help="Multiplies the client's net expenses. +10% means spending 10% more; -5% means spending 5% less.")
        if dp:
            st.caption(f"Net expenses ${base.net_expenses * (1 + dp / 100):,.0f} (client: ${base.net_expenses:,.0f})")
        st.button("Reset sliders", on_click=_reset, key=f"sc_reset_btn_{n}")
    overrides = S.build_overrides(base, sp, ss, rp, dp)
    eff, errs = S.apply_overrides(base, overrides)
    return eff, overrides, errs
