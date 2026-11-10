"""Streamlit UI.  Run:  streamlit run app/ui.py   (pip install streamlit)

Sidebar = grouped inputs with validation messages next to each field. Main panel = KPI cards, focus-year selector,
charts, projection table with column-group filters, and CSV / XLSX / HTML downloads.
"""
from __future__ import annotations
import io
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from PIL import Image

from app.branding_ui import apply_branding
from app.client_details import CLIENT_FIELDS, SIDEBAR_GROUPS, apply_pending_import, client_page, widget
from app.header import render_footer, render_header, render_title
from app.header_html import PRODUCT, favicon_path
from app.mortality_options import mortality_options
from app.scenario import describe as scenario_describe, warnings as scenario_warnings
from app.scenario_ui import render_scenario
from app.shell import current_view, settings_page
from app.sidebar_theme import apply_sidebar_theme
from app.ui_helpers import LABELS, form_to_inputs, to_form_values
from model import branding as B
from model import table_store as TS
from model.dashboard import Brand, build_figures, build_report_data, fmt_money, fmt_pct
from model.engine import ModelTables
from model.inputs import ProjectionInputs
from model.loop import ForwardTables
from model.parity import COLUMN_GROUPS
from model.report import build_html, scenario_table

def data_dir() -> str:
    return str(TS.effective_dir())

def _stamp(d: str) -> float:
    fs = list(Path(d).glob("*.csv"))
    return max((f.stat().st_mtime for f in fs), default=0.0)

@st.cache_resource
def _load_tables(data_dir_: str, stamp: float):
    return ModelTables.from_csv_dir(data_dir_), ForwardTables.from_csv_dir(data_dir_)

def load_tables():
    d = data_dir()
    return _load_tables(d, _stamp(d))

@st.cache_data(show_spinner="Running projection...")
def run_cached(inputs_json: str, as_of: str, scenarios: bool, tables_stamp: float):
    tables, ft = load_tables()
    inputs = ProjectionInputs(**json.loads(inputs_json))
    d = date.fromisoformat(as_of)
    rd = build_report_data(inputs, tables, ft, d)
    scen = scenario_table(inputs, tables, ft, d) if scenarios else None
    return rd, scen

def main():
    st.set_page_config(page_title=PRODUCT, page_icon=Image.open(favicon_path()), layout="wide")
    apply_branding(sidebar_logo=False)
    apply_sidebar_theme()
    tables, _ = load_tables()
    defaults = to_form_values(ProjectionInputs())
    store = st.session_state.setdefault("form", {f: defaults[f] for f in CLIENT_FIELDS})
    apply_pending_import(store)

    st.sidebar.image(str(B.logo_path("ribbon", dark_surface=True)), use_container_width=True)
    st.sidebar.title("Inputs")
    as_of = st.sidebar.date_input("Valuation date", value=date.today(), key="as_of")
    scen_box = st.sidebar.container()
    side, slots = {}, {}
    for group, fields in SIDEBAR_GROUPS.items():
        with st.sidebar.expander(group, expanded=group == "Mortality"):
            for f in fields:
                if f in ("inflation_scenario", "cola_scenario"):
                    cols = [c for c in tables.inflation_table.columns if c != "ForecastYr"]
                    side[f] = st.selectbox(LABELS[f], cols, index=cols.index(defaults[f]) if defaults[f] in cols else 0, key=f)
                elif f == "mortality_table":
                    opts = mortality_options(data_dir(), st.session_state.get("mortality_table"))
                    side[f] = st.selectbox(LABELS[f], opts, index=opts.index(defaults[f]) if defaults[f] in opts else 0, key=f)
                else:
                    side[f] = widget(f, defaults[f], f)
                slots[f] = st.empty()

    render_header()
    view = current_view()
    if view == "settings": settings_page(); render_footer(); st.stop()
    if view == "client": client_page(store, side, as_of); render_footer(); st.stop()

    inputs, errors = form_to_inputs({**side, **store})
    for f, msg in errors.items():
        (slots.get(f) or st.sidebar).error(f"{LABELS.get(f, f)}: {msg}")
    if inputs is None:
        st.error("Fix the highlighted inputs (open Client details with the head icon) to run the projection.")
        st.stop()

    with scen_box:
        base_inputs = inputs
        inputs, overrides, scen_errs = render_scenario(base_inputs, as_of)
    if inputs is None:
        for e in scen_errs:
            st.error(f"Scenario: {e}")
        st.stop()

    try:
        rd, scen = run_cached(inputs.model_dump_json(), as_of.isoformat(), True, _stamp(data_dir()))
    except KeyError as e:
        st.error(f"The model could not run with these inputs: {e}")
        st.stop()
    k = rd.kpis
    render_title(st.session_state.get("client_name", ""), as_of)
    if overrides:
        st.info("Scenario active: " + "; ".join(scenario_describe(base_inputs, overrides)) + ". Client inputs are unchanged.")
    for w in scenario_warnings(inputs, as_of):
        st.warning(w)
    if TS.is_customised():
        st.warning("Using edited model tables (data_user/). Results will not match the Excel reference.")

    #st.title("Retirement Forecast")#
    c = st.columns(5)
    c[0].metric("Funding ratio", fmt_pct(k["funding_ratio"]))
    c[1].metric("Surplus / (shortfall)", fmt_money(k["surplus"]))
    c[2].metric("Savings last through", "Beyond horizon" if k["fully_funded"] else f"Age {k['funded_through_age']}")
    c[3].metric("Peak resources", fmt_money(k["peak_assets"]), f"in {k['peak_asset_year']}")
    c[4].metric("Retirement", f"Age {k['retirement_age']}", f"{k['retirement_year']}")

    years = rd.view["B"].tolist()
    focus = st.select_slider("Focus year", options=years, value=years[min(13, len(years) - 1)])
    r = rd.df[rd.df["B"] == focus].iloc[0]
    f = st.columns(4)
    f[0].metric("Age", f"{int(r['C'])}")
    f[1].metric("Total resources", fmt_money(r["DH"]))
    f[2].metric("Net cash flow", fmt_money(r["CD"]))
    f[3].metric("Spending", fmt_money(r["G"] + r["H"]))

    figs = build_figures(rd, Brand(), scen)
    for name in ("assets_vs_liability", "cash_flow"):
        st.plotly_chart(figs[name], use_container_width=True)
    left, right = st.columns([1, 2])
    left.plotly_chart(figs["funding_gauge"], use_container_width=True)
    right.plotly_chart(figs["balance_sheet"], use_container_width=True)
    for name in ("asset_composition", "income_sources", "scenarios"):
        if name in figs:
            st.plotly_chart(figs[name], use_container_width=True)

    st.subheader("Projection table")
    groups = st.multiselect("Column groups", list(COLUMN_GROUPS), default=["Timeline", "Expenses", "Totals", "Surplus & cash flow"])
    cols = [c for g in groups for c in COLUMN_GROUPS[g] if c in rd.df.columns] or ["A", "B"]
    st.dataframe(rd.df[cols], use_container_width=True, height=360)

    d1, d2, d3 = st.columns(3)
    d1.download_button("Download CSV", rd.df.to_csv(index=False), "projection.csv", "text/csv")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        rd.df.to_excel(xw, sheet_name="Projection", index=False)
    d2.download_button("Download XLSX", buf.getvalue(), "projection.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    d3.download_button("Download HTML report", build_html(rd, figs, Brand()), "report.html", "text/html")
    render_footer()

if __name__ == "__main__":
    main()
