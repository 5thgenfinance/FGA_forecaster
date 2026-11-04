import json
from datetime import date
from pathlib import Path
import numpy as np, pandas as pd, pytest
import plotly.graph_objects as go

from model.engine import ModelTables
from model.loop import ForwardTables
from model.inputs import ProjectionInputs
from model.dashboard import (Brand, ReportData, build_report_data, build_figures, fmt_money, fmt_pct, fig_assets_vs_liability,
                             fig_cash_flow, fig_funding_gauge, fig_asset_composition, fig_income_sources, fig_balance_sheet,
                             fig_scenario_comparison, FIGURES)
from model.report import build_html, scenario_table, write_pngs, write_pdf, DISCLOSURES, assumptions_table
from app.cli import main as cli_main, format_validation_error, load_inputs
from app.ui_helpers import form_to_inputs, to_form_values, INPUT_GROUPS, field_kind

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASOF = date(2026, 11, 3)

@pytest.fixture(scope="module")
def tables(): return ModelTables.from_csv_dir(DATA)
@pytest.fixture(scope="module")
def ft(): return ForwardTables.from_csv_dir(DATA)
@pytest.fixture(scope="module")
def rd(tables, ft): return build_report_data(ProjectionInputs(), tables, ft, ASOF)
@pytest.fixture(scope="module")
def figs(rd): return build_figures(rd)

# ---- formatting / branding ----
def test_formatters():
    assert fmt_money(2_786_344) == "$2.79M" and fmt_money(-513_011) == "-$513K" and fmt_money(950) == "$950"
    assert fmt_money(1_234_567, compact=False) == "$1,234,567" and fmt_money(float("nan")) == "n/a" and fmt_money(2.5e9) == "$2.50B"
    assert fmt_pct(0.8445) == "84%" and fmt_pct(0.8445, 1) == "84.5%" and fmt_pct(float("nan")) == "n/a"

def test_brand_from_file(tmp_path):
    p = tmp_path / "b.json"; p.write_text(json.dumps({"firm_name": "Acme", "primary": "#000000", "palette": ["#111", "#222"]}))
    b = Brand.from_file(p)
    assert b.firm_name == "Acme" and b.primary == "#000000" and b.palette == ("#111", "#222") and b.accent == Brand().accent

def test_brand_rejects_unknown_keys(tmp_path):
    p = tmp_path / "b.json"; p.write_text(json.dumps({"firm_nam": "typo"}))
    with pytest.raises(ValueError, match="firm_nam"): Brand.from_file(p)

# ---- report data ----
def test_kpis_match_workbook_summary(rd):
    k = rd.kpis
    assert k["funding_ratio"] == pytest.approx(0.8445117631836683, rel=1e-9)
    assert k["surplus"] == pytest.approx(-513010.91947204946, abs=0.01)
    assert (k["retirement_year"], k["retirement_age"], k["ssi_start_year"], k["ssi_start_age"]) == (2029, 60, 2035, 67)
    assert k["peak_asset_year"] == 2066 and k["peak_assets"] == pytest.approx(10784289.9758, abs=0.01)
    assert k["first_unfunded_year"] == 2083 and k["funded_through_year"] == 2082 and not k["fully_funded"]

def test_chart_age_limit(tables, ft, rd):
    assert rd.view["C"].max() <= 100 and len(rd.view) < len(rd.df)
    full = build_report_data(ProjectionInputs(), tables, ft, ASOF, chart_age_limit=None)
    assert len(full.view) == len(full.df) == 64

# ---- figures ----
def test_all_figures_build_and_serialize(figs):
    assert set(figs) == set(FIGURES)
    for name, f in figs.items():
        assert isinstance(f, go.Figure) and len(f.data) >= 1
        assert json.loads(f.to_json())["layout"]["title"]["text"]

def test_every_figure_carries_the_disclaimer(figs):
    for name, f in figs.items():
        assert any("Hypothetical illustration" in (a.text or "") for a in f.layout.annotations), name

def test_assets_vs_liability_uses_DH_and_DF(rd):
    f = fig_assets_vs_liability(rd); v = rd.view
    np.testing.assert_allclose(f.data[0].y, v["DH"]); np.testing.assert_allclose(f.data[1].y, v["DF"])
    np.testing.assert_array_equal(f.data[0].x, v["B"])

def test_cash_flow_uses_net_cash_flow_and_signs(rd):
    f = fig_cash_flow(rd); v = rd.view
    np.testing.assert_allclose(f.data[0].y, v["CD"]); np.testing.assert_allclose(v["CD"], v["CX"])
    brand = Brand()
    assert all(c == (brand.positive if y >= 0 else brand.negative) for c, y in zip(f.data[0].marker.color, v["CD"]))

def test_gauge_value_and_range(rd):
    f = fig_funding_gauge(rd)
    assert f.data[0].value == pytest.approx(84.45117631836683) and f.data[0].gauge.axis.range[1] >= 150
    rich = ReportData(rd.df, rd.summary, rd.inputs, rd.as_of, dict(rd.kpis, funding_ratio=2.4))
    assert fig_funding_gauge(rich).data[0].gauge.axis.range[1] > 240

def test_composition_stack_sums_to_total_balances(rd):
    f = fig_asset_composition(rd)
    total = np.sum([np.asarray(t.y, float) for t in f.data], axis=0)
    np.testing.assert_allclose(total, rd.view["BV"], rtol=1e-9, atol=1e-6)

def test_income_sources_taxes_negative_and_spending_line(rd):
    f = fig_income_sources(rd); names = [t.name for t in f.data]
    tax = f.data[names.index("Income taxes")]
    assert (np.asarray(tax.y) <= 0).all()
    np.testing.assert_allclose(f.data[names.index("Spending")].y, rd.view["G"] + rd.view["H"])

def test_balance_sheet_bridges_to_surplus(rd):
    f = fig_balance_sheet(rd); y = np.asarray(f.data[0].y, float)
    assert y[:3].sum() == pytest.approx(rd.kpis["resources_pv"])
    assert y[3] == pytest.approx(rd.kpis["resources_pv"]) and y[4] == pytest.approx(-rd.kpis["need_pv"])
    assert y[5] == pytest.approx(rd.kpis["surplus"]) and y[3] + y[4] == pytest.approx(y[5])

def test_exhaustion_band_only_when_visible(tables, ft, rd):
    assert len(fig_cash_flow(rd).layout.shapes) <= 2          # default view stops at age 100 (before 2083)
    full = build_report_data(ProjectionInputs(), tables, ft, ASOF, chart_age_limit=None)
    assert any(s.type == "rect" for s in fig_cash_flow(full).layout.shapes)
    rich = build_report_data(ProjectionInputs(net_expenses=2000, brokerage=2_000_000), tables, ft, ASOF, chart_age_limit=None)
    assert rich.kpis["fully_funded"] and not any(s.type == "rect" for s in fig_cash_flow(rich).layout.shapes)

def test_scenario_comparison_requires_columns():
    with pytest.raises(ValueError): fig_scenario_comparison(pd.DataFrame({"x": [1]}))
    f = fig_scenario_comparison(pd.DataFrame({"label": ["Current plan", "B"], "funding_ratio": [0.8, 1.1]}), baseline="Current plan")
    assert list(f.data[0].x) == [80.0, 110.00000000000001] or np.allclose(f.data[0].x, [80, 110])

def test_scenario_table(tables, ft, rd):
    s = scenario_table(rd.inputs, tables, ft, ASOF)
    assert s.iloc[0]["label"] == "Current plan" and s.iloc[0]["funding_ratio"] == pytest.approx(rd.kpis["funding_ratio"])
    r = s.set_index("label")["funding_ratio"]
    assert r["Retire 2 years later"] > r["Current plan"] > r["Spend 10% more"]
    assert r["Interest rates 1 point higher"] > r["Current plan"] > r["Interest rates 1 point lower"]

# ---- HTML ----
def test_html_contents(rd, figs):
    h = build_html(rd, figs, Brand(firm_name="Acme Advisors"), client_name="Pat & Chris")
    assert "Acme Advisors" in h and "Pat &amp; Chris" in h and "2026-11-03" in h and "84%" in h
    for d in DISCLOSURES: assert d.split(".")[0][:40] in h
    for name in figs: assert f'id="{name}"' in h
    assert "cdn.plot.ly" in h or "plotly" in h.lower()
    assert "not a probability of success" in h

def test_html_escapes_untrusted_text(rd, figs):
    h = build_html(rd, figs, Brand(firm_name="<script>alert(1)</script>", extra_disclosure="<b>x</b>"), client_name="<img src=x>")
    assert "<script>alert(1)</script>" not in h and "<img src=x>" not in h and "&lt;script&gt;" in h and "&lt;b&gt;x&lt;/b&gt;" in h

def test_html_offline_embeds_plotly(rd, figs):
    assert len(build_html(rd, figs, offline=True)) > 1_000_000 > len(build_html(rd, figs, offline=False))

def test_assumptions_table_lists_scenarios(rd):
    rows = dict(assumptions_table(rd, "CPI70/COLA70", "legacy_treasury"))
    assert "CPI70/COLA70" in rows["Inflation assumption"] and "legacy_treasury" in rows["Discounting"]
    assert rows["Valuation date"] == "2026-11-03" and rows["Household"] == "Two people"

def test_single_person_and_well_funded_reports(tables, ft):
    one = build_report_data(ProjectionInputs(s_dob=None, t_s_ret_date=None), tables, ft, ASOF)
    assert "One person" in build_html(one, build_figures(one))
    rich = build_report_data(ProjectionInputs(net_expenses=2000, brokerage=2_000_000), tables, ft, ASOF)
    h = build_html(rich, build_figures(rich)); assert "Beyond age 100" in h

# ---- CLI ----
def run_cli(tmp_path, *extra, inputs=None):
    args = ["run", "--data", str(DATA), "--as-of", "2026-11-03", "--out", str(tmp_path / "out")]
    args += ["--inputs", str(inputs)] if inputs else ["--use-defaults"]
    return cli_main(args + list(extra))

def test_cli_writes_core_files(tmp_path):
    assert run_cli(tmp_path, "--client-name", "Test", "--scenarios") == 0
    out = tmp_path / "out"
    for f in ("projection.csv", "projection.xlsx", "summary.json", "report.html"): assert (out / f).stat().st_size > 0
    s = json.loads((out / "summary.json").read_text())
    assert s["summary"]["funding_ratio"] == pytest.approx(0.8445117631836683, rel=1e-9)
    assert s["summary"]["inflation_id"] == "CPI70/COLA70" and s["engine_version"] and s["adviser_notes"]
    assert s["inputs"]["salary"] == 110000 and s["kpis"]["first_unfunded_year"] == 2083
    csv = pd.read_csv(out / "projection.csv")
    assert len(csv) == 64 and {"A", "B", "DH", "CD", "UNFUNDED"} <= set(csv.columns)
    xl = pd.read_excel(out / "projection.xlsx", sheet_name=None)
    assert set(xl) == {"Projection", "KPIs", "Assumptions"} and len(xl["Projection"]) == 64
    assert 'id="scenarios"' in (out / "report.html").read_text()

def test_cli_reads_inputs_file_and_yaml(tmp_path):
    p = tmp_path / "in.json"; p.write_text(json.dumps({"net_expenses": 6000}))
    assert run_cli(tmp_path, inputs=p) == 0
    assert json.loads((tmp_path / "out" / "summary.json").read_text())["inputs"]["net_expenses"] == 6000
    y = tmp_path / "in.yaml"; y.write_text("net_expenses: 4000\nSSI_ret_age: 70\n")
    assert load_inputs(str(y)).SSI_ret_age == 70

def test_cli_invalid_inputs_exit_2_with_field_names(tmp_path, capsys):
    p = tmp_path / "bad.json"; p.write_text(json.dumps({"SSI_ret_age": 50, "salary": -1, "bogus": 1}))
    assert run_cli(tmp_path, inputs=p) == 2
    err = capsys.readouterr().err
    assert "SSI_ret_age" in err and "salary" in err and "bogus" in err
    assert not (tmp_path / "out" / "report.html").exists()

def test_cli_missing_or_broken_inputs_exit_3(tmp_path, capsys):
    assert cli_main(["run", "--data", str(DATA), "--out", str(tmp_path / "o")]) == 3
    assert run_cli(tmp_path, inputs=tmp_path / "nope.json") == 3
    p = tmp_path / "broken.json"; p.write_text("{not json")
    assert run_cli(tmp_path, inputs=p) == 3
    assert cli_main(["run", "--use-defaults", "--data", str(tmp_path / "no_data"), "--out", str(tmp_path / "o")]) == 3

def test_cli_bad_brand_file_exit_3(tmp_path):
    b = tmp_path / "b.json"; b.write_text(json.dumps({"nope": 1}))
    assert run_cli(tmp_path, "--brand", str(b)) == 3

def test_format_validation_error():
    with pytest.raises(Exception) as ei: ProjectionInputs(SSI_ret_age=50)
    assert any(l.startswith("SSI_ret_age:") for l in format_validation_error(ei.value))

# ---- optional image / PDF export (needs kaleido + Chrome) ----
@pytest.fixture(scope="module")
def pngs(figs, tmp_path_factory):
    paths, err = write_pngs({k: figs[k] for k in ("assets_vs_liability", "cash_flow")}, tmp_path_factory.mktemp("png"))
    if err: pytest.skip(f"image export unavailable: {err[:80]}")
    return paths

def test_png_export(pngs):
    assert len(pngs) == 2 and all(p.stat().st_size > 5000 and p.read_bytes()[:4] == b"\x89PNG" for p in pngs)

def test_pdf_export(rd, pngs, tmp_path):
    p = write_pdf(tmp_path / "r.pdf", rd, pngs, Brand(), "Pat")
    assert p.read_bytes()[:4] == b"%PDF" and p.stat().st_size > 10_000

def test_cli_png_pdf_flags(tmp_path):
    rc = run_cli(tmp_path, "--png", "--pdf")
    assert rc in (0, 4)                                        # 4 = optional export unavailable, core files still written
    assert (tmp_path / "out" / "report.html").exists()
    if rc == 0: assert (tmp_path / "out" / "report.pdf").exists() and (tmp_path / "out" / "charts" / "cash_flow.png").exists()

# ---- UI helpers ----
def test_form_round_trip():
    vals = to_form_values(ProjectionInputs())
    assert vals["LTRoR"] == pytest.approx(12.5) and vals["include_spouse"] is True
    inp, err = form_to_inputs(vals)
    assert err == {} and inp == ProjectionInputs()

def test_form_spouse_toggle_and_errors():
    vals = to_form_values(ProjectionInputs()); vals["include_spouse"] = False
    inp, err = form_to_inputs(vals); assert err == {} and inp.s_dob is None and not inp.joint
    vals["SSI_ret_age"] = 50; vals["salary"] = -5
    inp, err = form_to_inputs(vals)
    assert inp is None and {"SSI_ret_age", "salary"} <= set(err)

def test_every_form_field_is_known():
    fields = [f for g in INPUT_GROUPS.values() for f in g]
    assert len(fields) == len(set(fields))
    missing = set(ProjectionInputs.model_fields) - set(fields)
    assert missing == set(), missing
    for f in fields: assert field_kind(f) in {"bool", "date", "int", "float", "choice", "text"}
