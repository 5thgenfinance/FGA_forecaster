from datetime import date
from pathlib import Path
import json
import numpy as np, pandas as pd, pytest
from model.engine import ModelTables
from model.loop import ForwardTables
from model.pv import (run_projection, run_backward, dashboard_metrics, BACKWARD_COLUMNS, FEED_COLUMNS,
                      DASHBOARD_FEED_YEARS)
from model.inputs import ProjectionInputs
from model.curves import DiscountCurve
from model.scenarios import InflationScenario

DATA = Path(__file__).resolve().parents[1] / "data"
ASOF = date(2026, 11, 3)

@pytest.fixture(scope="module")
def tables(): return ModelTables.from_csv_dir(DATA)
@pytest.fixture(scope="module")
def ft(): return ForwardTables.from_csv_dir(DATA)
@pytest.fixture(scope="module")
def ref(): return pd.read_csv(DATA / "projection_reference.csv").apply(pd.to_numeric, errors="coerce")
@pytest.fixture(scope="module")
def expected(): return json.load(open(DATA / "summary_reference.json"))
@pytest.fixture(scope="module")
def run(tables, ft): return run_projection(ProjectionInputs(), tables, ft, ASOF, focus_year=2040)

@pytest.mark.parametrize("col", BACKWARD_COLUMNS + FEED_COLUMNS)
def test_column_parity(run, ref, col):
    df, _ = run
    a, b = df[col].to_numpy(float), ref[col].to_numpy(float)
    assert (np.isnan(a) == np.isnan(b)).all(), f"{col}: NaN pattern differs (Excel blanks/errors)"
    np.testing.assert_allclose(a[~np.isnan(a)], b[~np.isnan(b)], rtol=1e-9, atol=1e-6, err_msg=f"Projection!{col}")

def test_summary_matches_workbook(run, expected):
    _, s = run
    assert s["act_assets_C1"] == pytest.approx(expected["C1"], abs=0.01)
    assert s["act_liabilities_C2"] == pytest.approx(expected["C2"], abs=0.01)
    assert s["surplus_C3"] == pytest.approx(expected["C3"], abs=0.01)
    assert s["funding_ratio"] == pytest.approx(expected["funding_ratio"], rel=1e-9)
    assert s["balance_sheet_assets_F2"] == pytest.approx(expected["F2"], abs=0.01)
    assert s["balance_sheet_liabilities_F3"] == pytest.approx(expected["F3"], abs=0.01)
    assert s["projection_years"] == 64

def test_dashboard_milestones_match_workbook(run, expected):
    _, s = run
    assert s["peak_assets"] == pytest.approx(expected["peak_assets"], abs=0.01)
    assert s["peak_asset_year"] == expected["peak_asset_year"]
    assert s["lowest_assets"] == pytest.approx(expected["lowest_assets"], abs=0.01)
    assert s["first_positive_cash_flow_year"] == expected["first_positive_cash_flow_year"]

def test_focus_year_kpis_match_workbook(run, expected):
    _, s = run
    f = s["focus"]
    assert f["focus_year"] == expected["focus_year"]
    assert f["total_assets"] == pytest.approx(expected["focus_assets"], abs=0.01)
    assert f["net_cash_flow"] == pytest.approx(expected["focus_cash_flow"], abs=0.01)
    assert f["age"] == expected["focus_age"]
    assert f["expenses"] == pytest.approx(expected["focus_expenses"], abs=0.01)
    assert f["social_security"] == pytest.approx(expected["focus_social_security"], abs=0.01)
    assert f["investment_income"] == pytest.approx(expected["focus_investment_income"], abs=0.01)

# ---- identities and quirks ----
def test_c1_components(run):
    df, s = run
    assert s["act_assets_C1"] == pytest.approx(df["X"].iloc[0] + df["AK"].iloc[0] + df["BV"].iloc[0] * df["J"].iloc[0])
    assert s["surplus_C3"] == pytest.approx(s["act_assets_C1"] - s["act_liabilities_C2"])

def test_cc_is_yearly_surplus_not_c3(run):
    df, s = run
    np.testing.assert_allclose(df["CC"], df["AK"] + df["X"] + df["AF"] - df["P"])
    assert df["CC"].iloc[0] != pytest.approx(s["surplus_C3"])     # two surplus definitions are intentional (issue #8)

def test_year1_pv_columns_are_plain_sums(run):
    df, _ = run
    assert df["AK"].iloc[0] == pytest.approx(df["AJ"].sum())
    assert df["AR"].iloc[0] == pytest.approx(df["AQ"].sum())

def test_dashboard_pv_income_identity(run):
    df, _ = run
    feed = df.iloc[:DASHBOARD_FEED_YEARS]
    np.testing.assert_allclose(feed["DJ"], feed["AE"] + feed["AJ"] - feed["AQ"] + feed["CR"])
    np.testing.assert_allclose(feed["DH"], feed["CY"] + feed["DA"] + feed["DB"] + feed["DC"] + feed["DD"])

def test_feed_is_52_rows_by_default_and_full_on_request(tables, ft):
    a, sa = run_projection(ProjectionInputs(), tables, ft, ASOF)
    b, sb = run_projection(ProjectionInputs(), tables, ft, ASOF, feed_years=None)
    assert a["DH"].notna().sum() == 52 and b["DH"].notna().sum() == 64
    assert sa["feed_years"] == 52 and sb["feed_years"] == 64
    assert sb["peak_assets"] >= sa["peak_assets"]

def test_opening_dh_uses_opening_balances(run):
    df, _ = run
    assert df["DB"].iloc[0] == pytest.approx(300000)
    assert df["DD"].iloc[0] == pytest.approx(400000)
    assert df["DC"].iloc[0] == pytest.approx(150000 + 200000 + 25000 + 75000)

# ---- unfunded flag (new, not in Excel) ----
def test_unfunded_column(run):
    df, s = run
    assert (df["UNFUNDED"] >= 0).all() and s["first_unfunded_year"] == 2083
    np.testing.assert_allclose(df["UNFUNDED"], np.maximum(-df["CD"] - df["CQ"], 0))
    assert (df.loc[df["B"] < 2083, "UNFUNDED"] < 0.01).all()

# ---- assumptions are pluggable end-to-end ----
def test_higher_discount_rates_reduce_liabilities_and_assets_pv(tables, ft):
    base = run_projection(ProjectionInputs(), tables, ft, ASOF)[1]
    hi = run_projection(ProjectionInputs(), tables, ft, ASOF, curve=tables.legacy_curve().with_spread(0.01))[1]
    assert hi["act_liabilities_C2"] < base["act_liabilities_C2"]
    assert hi["act_assets_C1"] < base["act_assets_C1"]
    assert hi["curve_id"] != base["curve_id"]

def test_inflation_shift_hurts_funding_ratio(tables, ft):
    lo = run_projection(ProjectionInputs(), tables, ft, ASOF, inflation=inflation_scenario.constant(0.02, 0.02))[1]
    hi = run_projection(ProjectionInputs(), tables, ft, ASOF, inflation=inflation_scenario.constant(0.04, 0.02))[1]
    assert hi["funding_ratio"] < lo["funding_ratio"]
    assert hi["inflation_id"] == "constant"

def test_summary_records_scenario_ids(run):
    _, s = run
    assert s["inflation_id"] == "CPI70/COLA70" and s["curve_id"] == "legacy_treasury" and s["as_of_date"] == "2026-11-03"

# ---- dashboard helper ----
def test_focus_year_errors(run):
    df, _ = run
    with pytest.raises(ValueError): dashboard_metrics(df, 2010)
    with pytest.raises(ValueError): dashboard_metrics(df, 2085)     # beyond 52-row feed
    assert dashboard_metrics(df, 2027)["age"] == 59

# ---- variants ----
def test_single_person_projection(tables, ft):
    df, s = run_projection(ProjectionInputs(spouse_dob=None, spouse_target_ret_date=None), tables, ft, ASOF)
    assert np.isfinite(s["funding_ratio"]) and (df["DH"].dropna() >= 0).all()

def test_well_funded_plan_has_no_unfunded_years(tables, ft):
    inp = ProjectionInputs(net_expenses=2000, brokerage=2_000_000)
    _, s = run_projection(inp, tables, ft, ASOF)
    assert s["first_unfunded_year"] is None and s["funding_ratio"] > 1
