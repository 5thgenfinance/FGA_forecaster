"""Phase 6 - client visualizations (Plotly) built from the projection DataFrame.

Spec charts: assets-vs-liability line chart (Year/CW vs DH and DF) and net cash-flow columns (Year/CW vs CX).
Client extras: funding gauge, asset composition, income sources, balance-sheet bridge, scenario comparison.

The charts use the FULL projection horizon (feed_years=None) so the point where assets are exhausted is visible;
Excel's dashboard feed stops at 52 years. Headline funding numbers (C1, C2, C3) are unchanged by this.
"Total assets" (DH) in the Excel model = account balances + present value of Social Security + present value of
future earnings, so chart 1 is labelled "Total resources".
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .engine import ModelTables
from .inputs import ProjectionInputs
from .loop import ForwardTables
from .pv import run_projection

# ----------------------------------------------------------------------------- branding / formatting
@dataclass(frozen=True)
class Brand:
    firm_name: str = "FGA"
    report_title: str = "Retirement Forecast"
    tagline: str = ""
    primary: str = "#1F3A5F"
    accent: str = "#2A9D8F"
    positive: str = "#2E8B57"
    negative: str = "#C0392B"
    warning: str = "#E9A23B"
    neutral: str = "#6B7280"
    light: str = "#F3F5F8"
    font: str = "Helvetica, Arial, sans-serif"
    palette: tuple = ("#1F3A5F", "#2A9D8F", "#E9A23B", "#8E6C8A", "#5B8DB8", "#9CA3AF", "#C0392B")
    extra_disclosure: str = ""

    @classmethod
    def from_file(cls, path) -> "Brand":
        """Load overrides from a JSON file; unknown keys are rejected so typos do not pass silently."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        allowed = set(cls.__dataclass_fields__)
        bad = sorted(set(data) - allowed)
        if bad:
            raise ValueError(f"unknown brand keys: {', '.join(bad)}")
        if "palette" in data:
            data["palette"] = tuple(data["palette"])
        return cls(**data)

def fmt_money(x: float, compact: bool = True) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    sign = "-" if x < 0 else ""
    a = abs(float(x))
    if not compact:
        return f"{sign}${a:,.0f}"
    if a >= 1e9: return f"{sign}${a / 1e9:.2f}B"
    if a >= 1e6: return f"{sign}${a / 1e6:.2f}M"
    if a >= 1e3: return f"{sign}${a / 1e3:.0f}K"
    return f"{sign}${a:,.0f}"

def fmt_pct(x: float, digits: int = 0) -> str:
    return "n/a" if x is None or not np.isfinite(x) else f"{x * 100:.{digits}f}%"

SHORT_DISCLAIMER = "Hypothetical illustration based on stated assumptions; not a guarantee of future results."

# ----------------------------------------------------------------------------- report data
@dataclass
class ReportData:
    df: pd.DataFrame
    summary: dict
    inputs: ProjectionInputs
    as_of: date
    kpis: dict = field(default_factory=dict)
    chart_age_limit: int | None = 100     # charts stop when the primary client reaches this age (None = full horizon)

    @property
    def view(self) -> pd.DataFrame:
        """Rows shown in charts. KPIs and summary figures always use the full projection."""
        if self.chart_age_limit is None:
            return self.df
        v = self.df[self.df["C"] <= self.chart_age_limit]
        return v if len(v) else self.df

def _age_in_year(df: pd.DataFrame, year: int | None):
    if year is None:
        return None
    r = df.loc[df["B"] == year, "C"]
    return int(r.iloc[0]) if len(r) else None

def compute_kpis(df: pd.DataFrame, summary: dict, inputs: ProjectionInputs) -> dict:
    """Client-facing headline numbers from the full-horizon run."""
    last_year = int(df["B"].iloc[-1])
    unf = summary.get("first_unfunded_year")
    ssi = df.loc[df["V"] > 0, "B"]
    peak_i = int(df["DH"].to_numpy().argmax())
    funded_through = (unf - 1) if unf else last_year
    return {
        "funding_ratio": summary["funding_ratio"], "surplus": summary["surplus_C3"],
        "resources_pv": summary["act_assets_C1"], "need_pv": summary["act_liabilities_C2"],
        "retirement_year": inputs.t_ret_date.year,
        "retirement_age": int(inputs.t_ret_date.year - inputs.p_dob.year),
        "ssi_start_year": int(ssi.iloc[0]) if len(ssi) else None,
        "ssi_start_age": inputs.SSI_ret_age,
        "peak_assets": float(df["DH"].iloc[peak_i]), "peak_asset_year": int(df["B"].iloc[peak_i]),
        "first_unfunded_year": unf, "funded_through_year": funded_through,
        "funded_through_age": _age_in_year(df, funded_through), "fully_funded": unf is None,
        "last_year": last_year, "last_age": _age_in_year(df, last_year),
        "first_positive_cash_flow_year": summary.get("first_positive_cash_flow_year"),
    }

def build_report_data(inputs: ProjectionInputs, tables: ModelTables, ft: ForwardTables, as_of: date,
                      inflation=None, curve=None, chart_age_limit: int | None = 100, **kw) -> ReportData:
    df, summary = run_projection(inputs, tables, ft, as_of, inflation=inflation, curve=curve, feed_years=None, **kw)
    return ReportData(df, summary, inputs, as_of, compute_kpis(df, summary, inputs), chart_age_limit)

# ----------------------------------------------------------------------------- figure helpers
def _base_layout(fig: go.Figure, brand: Brand, title: str, subtitle: str = "", height: int = 460) -> go.Figure:
    text = f"<b>{title}</b>" + (f"<br><span style='font-size:12px;color:{brand.neutral}'>{subtitle}</span>" if subtitle else "")
    fig.update_layout(
        title=dict(text=text, x=0.01, xanchor="left"), height=height, template="plotly_white",
        font=dict(family=brand.font, size=13, color="#222"), margin=dict(l=70, r=30, t=90, b=125),
        legend=dict(orientation="h", y=-0.2, x=0), hovermode="x unified",
        annotations=list(fig.layout.annotations) + [dict(
            text=SHORT_DISCLAIMER, xref="paper", yref="paper", x=0, y=-0.34, showarrow=False, xanchor="left",
            font=dict(size=10, color=brand.neutral))])
    return fig

def _money_axis(fig: go.Figure, title: str = "") -> None:
    fig.update_yaxes(tickprefix="$", tickformat=".2s", title_text=title, gridcolor="#E5E7EB", zerolinecolor="#9CA3AF")
    fig.update_xaxes(showgrid=False, dtick=5)

def _vmarker(fig: go.Figure, year, text: str, color: str, ypos: float = 1.0) -> None:
    if year is None:
        return
    fig.add_vline(x=year, line_dash="dot", line_color=color, line_width=1.5)
    fig.add_annotation(x=year, y=ypos, yref="paper", text=text, showarrow=False, xanchor="left", yanchor="bottom",
                       font=dict(size=11, color=color), bgcolor="rgba(255,255,255,0.8)")

def _exhaustion_band(fig: go.Figure, rd: ReportData, brand: Brand) -> None:
    unf = rd.kpis["first_unfunded_year"]
    last = int(rd.view["B"].iloc[-1])
    if unf is not None and unf <= last:
        fig.add_vrect(x0=unf - 0.5, x1=last + 0.5, fillcolor=brand.negative, opacity=0.08, line_width=0)
        fig.add_annotation(x=unf, y=0.02, yref="paper", text="Savings exhausted", showarrow=False, xanchor="left",
                           font=dict(size=11, color=brand.negative))

def _markers(fig: go.Figure, rd: ReportData, brand: Brand) -> None:
    k = rd.kpis
    _vmarker(fig, k["retirement_year"], f"Retirement ({k['retirement_age']})", brand.primary, 1.0)
    if k["ssi_start_year"] and k["ssi_start_year"] != k["retirement_year"]:
        _vmarker(fig, k["ssi_start_year"], f"Social Security ({k['ssi_start_age']})", brand.accent, 0.93)

# ----------------------------------------------------------------------------- the charts
def fig_assets_vs_liability(rd: ReportData, brand: Brand = Brand()) -> go.Figure:
    """Spec chart 1: Year (CW) vs Total resources (DH) and lifetime spending need / SOL liability (DF)."""
    df = rd.view
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["B"], y=df["DH"], name="Total resources", mode="lines",
                             line=dict(color=brand.primary, width=3), hovertemplate="%{y:$,.0f}"))
    fig.add_trace(go.Scatter(x=df["B"], y=df["DF"], name="Lifetime spending need", mode="lines",
                             line=dict(color=brand.warning, width=3, dash="dash"), hovertemplate="%{y:$,.0f}"))
    pi = int(df["DH"].to_numpy().argmax())
    fig.add_trace(go.Scatter(x=[df["B"].iloc[pi]], y=[df["DH"].iloc[pi]], mode="markers+text", name="Peak",
                             marker=dict(color=brand.primary, size=10), text=[f"Peak {fmt_money(df['DH'].iloc[pi])}"],
                             textposition="top center", showlegend=False, hoverinfo="skip"))
    _markers(fig, rd, brand); _exhaustion_band(fig, rd, brand); _money_axis(fig)
    return _base_layout(fig, brand, "Resources vs. lifetime spending need",
                        "Resources include savings plus the present value of Social Security and future earnings")

def fig_cash_flow(rd: ReportData, brand: Brand = Brand()) -> go.Figure:
    """Spec chart 2: Year (CW) vs Net cash flow (CX) as columns."""
    df = rd.view
    colors = np.where(df["CD"] >= 0, brand.positive, brand.negative)
    fig = go.Figure(go.Bar(x=df["B"], y=df["CD"], marker_color=colors, name="Net cash flow",
                           hovertemplate="%{y:$,.0f}"))
    _markers(fig, rd, brand); _exhaustion_band(fig, rd, brand); _money_axis(fig)
    return _base_layout(fig, brand, "Net cash flow by year",
                        "Income after tax minus spending. Green years add to savings; red years draw on savings")

def fig_funding_gauge(rd: ReportData, brand: Brand = Brand()) -> go.Figure:
    """Funding ratio = PV of resources / PV of lifetime spending need (not a probability of success)."""
    ratio = rd.kpis["funding_ratio"] * 100
    top = max(150.0, np.ceil(ratio / 25) * 25 + 25) if np.isfinite(ratio) else 150.0
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=ratio if np.isfinite(ratio) else 0,
        number=dict(suffix="%", valueformat=".0f", font=dict(size=54, color=brand.primary)),
        gauge=dict(axis=dict(range=[0, top], ticksuffix="%"), bar=dict(color=brand.primary, thickness=0.28),
                   steps=[dict(range=[0, 75], color="#F4C7C3"), dict(range=[75, 100], color="#FBE3B8"),
                          dict(range=[100, top], color="#C9E7D4")],
                   threshold=dict(line=dict(color="#111", width=4), thickness=0.8, value=100))))
    fig.update_layout(annotations=[dict(
        text="Present value of resources divided by present value of lifetime spending. "
             "100% means fully funded under these assumptions; it is not a probability of success.",
        xref="paper", yref="paper", x=0.5, y=-0.12, showarrow=False, font=dict(size=11, color=brand.neutral))])
    return _base_layout(fig, brand, "Funding ratio", height=380)

ACCOUNT_STACK = [("Pre-tax (401k / IRA)", ["AT", "AU", "AY"]), ("Roth / after-tax 401k", ["BJ", "BI"]),
                 ("Taxable brokerage", ["BM"]), ("Sleeve 3", ["BK"]), ("Cash reserve", ["BL"]), ("Real assets", ["BN"])]

def fig_asset_composition(rd: ReportData, brand: Brand = Brand()) -> go.Figure:
    """Year-end account balances by type (excludes present values of Social Security / earnings)."""
    df = rd.view
    fig = go.Figure()
    for (name, cols), color in zip(ACCOUNT_STACK, brand.palette):
        fig.add_trace(go.Scatter(x=df["B"], y=df[cols].sum(axis=1), name=name, mode="lines", stackgroup="one",
                                 line=dict(width=0.5, color=color), fillcolor=color, hovertemplate="%{y:$,.0f}"))
    _markers(fig, rd, brand); _exhaustion_band(fig, rd, brand); _money_axis(fig)
    return _base_layout(fig, brand, "Where your savings sit over time", "Projected year-end account balances")

def fig_income_sources(rd: ReportData, brand: Brand = Brand()) -> go.Figure:
    """Annual income by source (bars), taxes (negative) and spending (line)."""
    df = rd.view
    series = [("Salary and earnings", df["AC"] + df["AD"], brand.palette[0]),
              ("Social Security", df["V"], brand.palette[1]),
              ("Sleeve 3 income", df["AI"], brand.palette[2]),
              ("IRA distributions", df["BD"] + df["BE"], brand.palette[3]),
              ("Savings withdrawals", df["CQ"], brand.palette[4]),
              ("Income taxes", -df["AO"], brand.palette[6])]
    fig = go.Figure()
    for name, y, color in series:
        fig.add_trace(go.Bar(x=df["B"], y=y, name=name, marker_color=color, hovertemplate="%{y:$,.0f}"))
    fig.add_trace(go.Scatter(x=df["B"], y=df["G"] + df["H"], name="Spending", mode="lines",
                             line=dict(color="#111", width=2.5), hovertemplate="%{y:$,.0f}"))
    fig.update_layout(barmode="relative")
    _markers(fig, rd, brand); _exhaustion_band(fig, rd, brand); _money_axis(fig)
    return _base_layout(fig, brand, "Where your income comes from", "Annual income by source, estimated federal tax, and spending")

def fig_balance_sheet(rd: ReportData, brand: Brand = Brand()) -> go.Figure:
    """Bridge from present-value resources to the lifetime spending need (Projection C1, C2, C3)."""
    df, k = rd.df, rd.kpis
    items = [("Social Security", df["X"].iloc[0]), ("Sleeve 3 income", df["AK"].iloc[0]),
             ("Savings and accounts", df["BW"].iloc[0])]
    labels = [n for n, _ in items] + ["Total resources", "Lifetime spending need", "Surplus / (shortfall)"]
    vals = [v for _, v in items] + [k["resources_pv"], -k["need_pv"], k["surplus"]]
    fig = go.Figure(go.Waterfall(
        x=labels, y=vals, measure=["relative"] * 3 + ["total", "relative", "total"],
        text=[fmt_money(v) for v in vals], textposition="outside",
        increasing=dict(marker_color=brand.positive), decreasing=dict(marker_color=brand.negative),
        totals=dict(marker_color=brand.primary), connector=dict(line=dict(color="#9CA3AF"))))
    _money_axis(fig); fig.update_layout(showlegend=False, hovermode="closest")
    return _base_layout(fig, brand, "Funding bridge (present values)", "Today's value of everything available vs. everything planned")

def fig_scenario_comparison(rows: pd.DataFrame, brand: Brand = Brand(), baseline: str | None = None) -> go.Figure:
    """Funding ratio by scenario. `rows` needs columns `label` and `funding_ratio`."""
    if not {"label", "funding_ratio"} <= set(rows.columns):
        raise ValueError("rows needs 'label' and 'funding_ratio' columns")
    r = rows.dropna(subset=["funding_ratio"])
    colors = [brand.primary if lbl == baseline else (brand.positive if v >= 1 else brand.warning)
              for lbl, v in zip(r["label"], r["funding_ratio"])]
    fig = go.Figure(go.Bar(x=r["funding_ratio"] * 100, y=r["label"], orientation="h", marker_color=colors,
                           text=[fmt_pct(v) for v in r["funding_ratio"]], textposition="outside"))
    fig.add_vline(x=100, line_dash="dash", line_color="#111")
    fig.update_xaxes(ticksuffix="%", gridcolor="#E5E7EB"); fig.update_yaxes(autorange="reversed")
    fig.update_layout(hovermode="closest", showlegend=False)
    return _base_layout(fig, brand, "How the plan responds to different assumptions", "Funding ratio; 100% = fully funded",
                        height=max(380, 60 + 38 * len(r)))

FIGURES = {"assets_vs_liability": fig_assets_vs_liability, "cash_flow": fig_cash_flow, "funding_gauge": fig_funding_gauge,
           "asset_composition": fig_asset_composition, "income_sources": fig_income_sources, "balance_sheet": fig_balance_sheet}

def build_figures(rd: ReportData, brand: Brand = Brand(), scenarios: pd.DataFrame | None = None) -> dict:
    figs = {name: fn(rd, brand) for name, fn in FIGURES.items()}
    if scenarios is not None and len(scenarios):
        figs["scenarios"] = fig_scenario_comparison(scenarios, brand, baseline="Current plan")
    return figs
