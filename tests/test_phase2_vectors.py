from datetime import date
from pathlib import Path
import numpy as np, pandas as pd, pytest
from model.engine import (ModelTables, run_vectors, build_discount_table, VECTOR_COLUMNS)
from model.inputs import ProjectionInputs
from model.curves import DiscountCurve
from model.scenarios import InflationScenario

DATA = Path(__file__).resolve().parents[1] / "data"
ASOF = date(2026, 11, 3)

@pytest.fixture(scope="module")
def tables(): return ModelTables.from_csv_dir(DATA)
@pytest.fixture(scope="module")
def ref(): return pd.read_csv(DATA / "projection_reference.csv")
@pytest.fixture(scope="module")
def run(tables): return run_vectors(ProjectionInputs(), tables, ASOF)

@pytest.mark.parametrize("col", VECTOR_COLUMNS)
def test_column_parity(run, ref, col):
    df, _ = run
    np.testing.assert_allclose(df[col].to_numpy(float), ref[col].to_numpy(float), rtol=1e-9, atol=1e-6,
                               err_msg=f"Projection!{col}")

def test_shape_and_horizon(run):
    df, meta = run
    assert len(df) == 64 and meta["n_years"] == 64 and list(df.columns) == VECTOR_COLUMNS
    assert df["B"].iloc[0] == 2027 and meta["valuation_date"] == "2029-03-28"

def test_headline_reserve_matches_workbook_C2(run):
    _, meta = run
    assert meta["reserve_P1"] == pytest.approx(3299355.1793762785, abs=0.01)

def test_discount_table_matches_workbook(tables):
    dr = pd.read_csv(DATA / "tblDiscountRates.csv")
    dt = build_discount_table(tables.legacy_curve(), 0.015)
    for c in ["ExpenseDiscountRt", "SSIDiscountRt", "EmploymentDiscountRt", "ExpDiscFact", "SSIDiscFact", "EmpDiscFact"]:
        np.testing.assert_allclose(dt[c], dr[c], rtol=1e-9, atol=1e-12, err_msg=c)

def test_bt_quirk_is_latent_for_default_case(tables, run):
    """Mortgage is paid off by year 5, so the BT19+ divisor quirk has no numeric effect by default."""
    fixed, _ = run_vectors(ProjectionInputs(), tables, ASOF, legacy_quirks=False)
    pd.testing.assert_frame_equal(run[0], fixed)

def test_bt_legacy_quirk_isolated_for_long_mortgage(tables):
    inp = ProjectionInputs(mort_payments=360)
    legacy, _ = run_vectors(inp, tables, ASOF)
    fixed, meta = run_vectors(inp, tables, ASOF, legacy_quirks=False)
    assert meta["legacy_quirks"] is False
    other = [c for c in VECTOR_COLUMNS if c != "BT"]
    pd.testing.assert_frame_equal(legacy[other], fixed[other])
    changed = ~np.isclose(legacy["BT"], fixed["BT"])
    assert not changed[:12].any() and changed[12:].any()      # years 13+ differ (rows 19+)

def test_expense_and_pv_identities(run):
    df, _ = run
    assert (df["G"] * 1.0).iloc[0] == pytest.approx(12 * 5000 * df["E"].iloc[0])
    assert np.allclose(df["O"], df["L"] * df["G"] * df["M"])
    assert df["P"].iloc[0] == pytest.approx(df["O"].sum())
    assert df["Y"].iloc[0] == pytest.approx(df["X"].iloc[0] - df["P"].iloc[0])

# ---- pluggable assumptions ----
def test_flat_curve_changes_liability_in_expected_direction(tables):
    base = run_vectors(ProjectionInputs(), tables, ASOF)[1]["reserve_P1"]
    low = run_vectors(ProjectionInputs(), tables, ASOF, curve=DiscountCurve("flat3", (1.0, 30.0), (0.03, 0.03)))[1]["reserve_P1"]
    high = run_vectors(ProjectionInputs(), tables, ASOF, curve=DiscountCurve("flat7", (1.0, 30.0), (0.07, 0.07)))[1]["reserve_P1"]
    assert high < base < low

def test_curve_shift_matches_parallel_rates(tables):
    c = tables.legacy_curve()
    up = c.with_spread(0.01)
    assert run_vectors(ProjectionInputs(), tables, ASOF, curve=up)[1]["curve_id"] == up.id
    assert run_vectors(ProjectionInputs(), tables, ASOF, curve=up)[1]["reserve_P1"] < run_vectors(ProjectionInputs(), tables, ASOF)[1]["reserve_P1"]

def test_higher_inflation_raises_expense_reserve(tables):
    lo = run_vectors(ProjectionInputs(), tables, ASOF, inflation=InflationScenario.constant(0.02, 0.02))[1]["reserve_P1"]
    hi = run_vectors(ProjectionInputs(), tables, ASOF, inflation=InflationScenario.constant(0.04, 0.02))[1]["reserve_P1"]
    assert hi > lo

def test_zero_cola_keeps_ssi_flat(tables):
    df, _ = run_vectors(ProjectionInputs(), tables, ASOF, inflation=InflationScenario.constant(0.03, 0.0))
    paid = df.loc[df["V"] > 0, "V"]
    assert paid.nunique() == 1 and paid.iloc[0] == pytest.approx(3050 * 12)

def test_scenario_too_short_raises(tables):
    with pytest.raises(ValueError): run_vectors(ProjectionInputs(), tables, ASOF, inflation=InflationScenario.constant(0.03, n=30))

def test_unknown_legacy_scenario_name(tables):
    with pytest.raises(KeyError): tables.legacy_inflation("NOPE", "COLA70")

# ---- input variants ----
def test_single_person_runs(tables):
    df, meta = run_vectors(ProjectionInputs(s_dob=None, t_s_ret_date=None), tables, ASOF)
    assert df["D"].isna().all() and meta["n_years"] > 0
    assert (df["I"].diff().dropna() <= 1e-12).all()

def test_no_mortgage(tables):
    df, _ = run_vectors(ProjectionInputs(mortgage=0), tables, ASOF)
    assert (df["BQ"] == 0).all() and (df["BS"] == 0).all()

def test_mortgage_payments_stop(run):
    df, _ = run
    assert (df["BQ"].iloc[:5] > 0).all() and (df["BQ"].iloc[5:] == 0).all()

def test_retired_status_uses_as_of_date(tables):
    _, meta = run_vectors(ProjectionInputs(retired="RETIRED", t_ret_date=date(2026, 1, 1)), tables, ASOF)
    assert meta["valuation_date"] == "2026-11-03"
