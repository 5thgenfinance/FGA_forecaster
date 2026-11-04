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

from app.ui_helpers import HELP, INPUT_GROUPS, LABELS, PCT_FIELDS, choices, field_kind, form_to_inputs, to_form_values
from model.dashboard import Brand, build_figures, build_report_data, fmt_money, fmt_pct
from model.engine import ModelTables
from model.inputs import ProjectionInputs
from model.loop import ForwardTables
from model.parity import COLUMN_GROUPS
from model.report import build_html, scenario_table

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@st.cache_resource
def load_tables(data_dir: str):
    return ModelTables.from_csv_dir(data_dir), ForwardTables.from_csv_dir(data_dir)

@st.cache_data(show_spinner="Running projection...")
def run_cached(inputs_json: str, as_of: str, scenarios: bool):
    tables, ft = load_tables(str(DATA_DIR))
    inputs = ProjectionInputs(**json.loads(inputs_json))
    d = date.fromisoformat(as_of)
    rd = build_report_data(inputs, tables, ft, d)
    scen = scenario_table(inputs, tables, ft, d) if scenarios else None
    return rd, scen

def widget(name: str, default, key: str):
    label, kind, help_ = LABELS.get(name, name), field_kind(name), HELP.get(name)
    if kind == "bool":
        return st.checkbox(label, value=bool(default), key=key, help=help_)
    if kind == "date":
        return st.date_input(label, value=default or date(1970, 1, 1), min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key=key, help=help_)
    if kind == "int":
        return st.number_input(label, value=int(default), step=1, key=key, help=help_)
    if kind == "float":
        step = 0.1 if name in PCT_FIELDS else 1000.0
        return st.number_input(label, value=float(default), step=step, key=key, help=help_)
    if kind == "choice":
        opts = choices(name)
        return st.selectbox(label, opts, index=opts.index(default) if default in opts else 0, key=key, help=help_)
    return st.text_input(label, value=str(default), key=key, help=help_)

def main():
    st.set_page_config(page_title="Retirement Forecast", layout="wide")
    tables, _ = load_tables(str(DATA_DIR))
    defaults = to_form_values(ProjectionInputs())
    st.sidebar.title("Inputs")
    as_of = st.sidebar.date_input("Valuation date", value=date.today())
    values, slots = {}, {}
    for group, fields in INPUT_GROUPS.items():
        with st.sidebar.expander(group, expanded=group == "Personal"):
            for f in fields:
                if f in ("s_dob", "t_s_ret_date") and not values.get("include_spouse", True):
                    continue
                if f in ("InflationScenario", "COLAScenario"):
                    cols = [c for c in tables.inflation_table.columns if c != "ForecastYr"]
                    values[f] = st.selectbox(LABELS[f], cols, index=cols.index(defaults[f]) if defaults[f] in cols else 0, key=f)
                else:
                    values[f] = widget(f, defaults[f], f)
                slots[f] = st.empty()
    inputs, errors = form_to_inputs(values)
    for f, msg in errors.items():
        (slots.get(f) or st.sidebar).error(f"{LABELS.get(f, f)}: {msg}")
    if inputs is None:
        st.error("Fix the highlighted inputs to run the projection.")
        st.stop()

    rd, scen = run_cached(inputs.model_dump_json(), as_of.isoformat(), True)
    k = rd.kpis
    st.title("Retirement Forecast")
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
    st.caption("Hypothetical illustration based on stated assumptions; not a guarantee of future results.")

if __name__ == "__main__":
    main()
