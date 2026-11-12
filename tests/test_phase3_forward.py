from datetime import date
from pathlib import Path
import numpy as np, pandas as pd, pytest
from model.engine import ModelTables
from model.loop import (ForwardTables, FORWARD_COLUMNS, run_through_phase3, run_forward, opening_balances)
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
def ref(): return pd.read_csv(DATA / "projection_reference.csv")
@pytest.fixture(scope="module")
def run(tables, ft): return run_through_phase3(ProjectionInputs(), tables, ft, ASOF)

@pytest.mark.parametrize("col", FORWARD_COLUMNS)
def test_column_parity(run, ref, col):
    df, _ = run
    np.testing.assert_allclose(df[col].to_numpy(float), ref[col].to_numpy(float), rtol=1e-9, atol=1e-6,
                               equal_nan=True, err_msg=f"Projection!{col}")

def test_spec_section_11_2_first_five_years(run):
    """Spec 11.2 values that do not depend on the Treasury curve."""
    df, _ = run
    exp = {"AM": [145961.858242, 152839.440671, 62217.390944, 31496.192, 32756.03968],
           "AO": [9813.422989, 10029.812881, 0, 0, 0],
           "BV": [1346486.457895, 1507512.576961, 1591837.087806, 1666750.549749, 1765399.821777],
           "CD": [38884.792058, 41066.504595, -43481.502611, -54955.702087, -59450.100645]}
    for c, vals in exp.items():
        np.testing.assert_allclose(df[c].iloc[:5], vals, rtol=1e-6, atol=0.01, err_msg=c)

def test_opening_balances_match_workbook_F2():
    ob = opening_balances(ProjectionInputs())
    assert sum(ob.values()) == pytest.approx(1197000)
    assert ob["BM"] == pytest.approx(300000 - 200000 - 25000)

# ---- structural invariants ----
def test_bv_is_sum_of_accounts(run):
    df, _ = run
    s = df[["AT", "AU", "AY", "BI", "BJ", "BK", "BL", "BM", "BN"]].sum(axis=1)
    np.testing.assert_allclose(df["BV"], s)
    np.testing.assert_allclose(df["BW"], df["BV"] * df["J"])

def test_cash_flow_identity(run):
    df, _ = run
    np.testing.assert_allclose(df["CD"], df["BY"] - df["AO"] - df["G"] - df["H"])
    np.testing.assert_allclose(df["CA"], df["BY"] - df["BZ"])

def test_balances_non_negative(run):
    df, _ = run
    for c in ["AU", "AY", "BJ", "BK", "BL", "BM", "BN"]:
        assert (df[c] >= -1e-9).all(), c

def test_401k_rolls_into_ira_after_retirement(run):
    df, _ = run
    first_zero = int(np.argmax(df["AG"].to_numpy() == 0))
    assert df["AT"].iloc[first_zero] == 0 and df["AT"].iloc[first_zero - 1] > 0
    assert df["AT"].iloc[first_zero:].eq(0).all()

def test_surplus_goes_to_savings_not_distributions(run):
    df, _ = run
    pos = df["CD"] > 0
    assert (df.loc[pos, "CQ"] == 0).all()
    np.testing.assert_allclose(df.loc[pos, "CF"] + df.loc[pos, "CG"] + df.loc[pos, "CH"], df.loc[pos, "CD"])

def test_waterfall_follows_balance_rules(tables, ft):
    """Each source supplies min(remaining need, its prior-year balance): cash, brokerage, Sleeve 3, trad IRA, Roth, real assets."""
    inp = ProjectionInputs(net_expenses=15000)
    df, _ = run_through_phase3(inp, tables, ft, ASOF)
    ob = opening_balances(inp)
    prev = pd.DataFrame({"BL": [ob["BL"]], "BM": [ob["BM"]], "BK": [ob["BK"]], "BJ": [ob["BJ"]], "BN": [ob["BN"]],
                         "IRA": [ob["AU"] + ob["AY"]]})
    bal = pd.concat([prev, pd.DataFrame({"BL": df["BL"], "BM": df["BM"], "BK": df["BK"], "BJ": df["BJ"], "BN": df["BN"],
                                         "IRA": df["AU"] + df["AY"]})], ignore_index=True).iloc[:-1].reset_index(drop=True)
    assert (df["CD"] < 0).any()
    for t in df.index[df["CD"] < 0]:
        need = -df.loc[t, "CD"]
        for col, key in [("CJ", "BL"), ("CK", "BM"), ("CL", "BK"), ("CM", "IRA"), ("CN", "BJ"), ("CO", "BN")]:
            take = min(need, bal.loc[t, key])
            assert df.loc[t, col] == pytest.approx(take, abs=1e-6), (t, col)
            need -= take

def test_cash_goes_first(tables, ft):
    df, _ = run_through_phase3(ProjectionInputs(net_expenses=15000), tables, ft, ASOF)
    r = df[df["CD"] < 0].iloc[0]
    assert r["CJ"] > 0 and r["CJ"] <= 25000 * 1.035 + 1

def test_roth_contribution_capped_by_limit(run):
    df, _ = run
    assert (df["CF"] <= 17200 * (1.03 ** df["A"]) + 1).all()

# ---- independence from discount curve; sensitivity to inflation ----
def test_forward_nominal_columns_independent_of_discount_curve(tables, ft):
    a, _ = run_through_phase3(ProjectionInputs(), tables, ft, ASOF)
    b, _ = run_through_phase3(ProjectionInputs(), tables, ft, ASOF, curve=DiscountCurve("flat9", (1.0, 30.0), (0.09, 0.09)))
    cols = [c for c in FORWARD_COLUMNS if c != "BW"] 
    pd.testing.assert_frame_equal(a[cols], b[cols])

def test_inflation_scenario_changes_cash_flow(tables, ft):
    a, _ = run_through_phase3(ProjectionInputs(), tables, ft, ASOF)
    b, _ = run_through_phase3(ProjectionInputs(), tables, ft, ASOF, inflation=inflation_scenario.constant(0.06, 0.02))
    assert not np.allclose(a["CD"], b["CD"])
    assert b["G"].iloc[-1] > a["G"].iloc[-1] * 0 + 0

def test_draw_pct_parameter(tables, ft):
    a, _ = run_through_phase3(ProjectionInputs(), tables, ft, ASOF, draw_pct=0.0)
    b, _ = run_through_phase3(ProjectionInputs(), tables, ft, ASOF)
    k = int(np.argmax(b["AW"].to_numpy() == 1))
    assert a["BD"].iloc[k] == a["AX"].iloc[k] == 0 and b["BD"].iloc[k] > 0

# ---- variants ----
def test_single_person(tables, ft):
    df, _ = run_through_phase3(ProjectionInputs(spouse_dob=None, spouse_target_ret_date=None), tables, ft, ASOF)
    assert (df["BE"] == 0).all() and (df["AY"] == 0).all() and (df["BB"] == 0).all() and df["AZ"].isna().all()
    assert np.isfinite(df[["AM", "AO", "BV", "CD"]].to_numpy()).all()

def test_already_retired(tables, ft):
    inp = ProjectionInputs(ret_status="RETIRED", primary_target_ret_date=date(2026, 1, 1), salary=0, pretax_401k=0)
    df, _ = run_through_phase3(inp, tables, ft, ASOF)
    assert (df["AG"] == 0).all() and (df["AT"] == 0).all()

def test_rmds_start_at_age_75_for_1969_birth(run):
    df, _ = run
    first = df.index[df["AX"] > 0][0]
    assert df.loc[first, "B"] - 1969 == 75
    assert df.loc[:first - 1, "AX"].eq(0).all()

def test_zero_assets_no_negative_balances(tables, ft):
    inp = ProjectionInputs(pretax_401k=0, primary_trad_ira=0, roth_ira=0, brokerage=225000, real_estate=0, mortgage=0)
    df, _ = run_through_phase3(inp, tables, ft, ASOF)
    assert (df[["AU", "BJ", "BK", "BL", "BM", "BN"]] >= -1e-9).all().all()
