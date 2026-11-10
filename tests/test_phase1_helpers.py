from datetime import date
from pathlib import Path
import numpy as np, pandas as pd, pytest
from model import helpers as H, tax as T, mortality as M
from model.curves import DiscountCurve
from model.scenarios import InflationScenario
from model.inputs import ProjectionInputs

DATA = Path(__file__).resolve().parents[1] / "data"
ASOF = date(2026, 11, 3)
rd = lambda n: pd.read_csv(DATA / f"{n}.csv")

@pytest.fixture(scope="module")
def tax(): return T.TaxTables(rd("tblTax"), rd("tblLTGCtax"))
@pytest.fixture(scope="module")
def mort(): return M.MortalityTable(rd("tblMortality"))
@pytest.fixture(scope="module")
def ref(): return rd("projection_reference")

# ---- workbook reference vectors (Main!C4:C9, E50, B59; SSIdata!F1,F3) ----
def test_retireage(): assert H.retire_age(date(1969, 3, 28), date(2029, 3, 28)) == 60
def test_taxest(tax): assert T.tax_est(tax, 110000, 0, True, 0.04, 1) == pytest.approx(8665.6, abs=0.01)
def test_rmd_zero():
    lurmd = dict(zip(rd("tblLURMD").attained_age, rd("tblLURMD").factor))
    assert H.rmd(date(1969, 3, 28), 2027, 347000, lurmd) == 0
@pytest.mark.parametrize("sleeve,aum,fee", [(1, 33000, 0), (2, 200000, 1500), (3, 100000, 750), (4, 150000, 1875), (5, 150000, 1875)])
def test_sleevefee(sleeve, aum, fee): assert T.sleeve_fee(sleeve, aum) == pytest.approx(fee)
def test_ss_aime_pia():
    aime = T.ss_aime(range(130000, 167000, 1000))
    assert aime == 12416 and T.ss_pia(aime, 1286, 7749) == pytest.approx(3925.6)
def test_expected_life(mort):
    px = H.age_nearest(date(1969, 3, 28), date(2029, 3, 28))
    assert M.expected_life(mort, "IAM2012M", "IAM2012F", "M", px) == pytest.approx(26.04093226740233, rel=1e-9)
    sx = H.age_nearest(date(1971, 1, 1), date(2029, 3, 28))
    assert M.expected_life(mort, "IAM2012M", "IAM2012F", "F", sx) == pytest.approx(29.931390058485775, rel=1e-9)
    assert M.expected_life_joint(mort, "IAM2012M", "IAM2012F", "M", "F", px, sx, "last_survivor") == pytest.approx(33.77483875106366, rel=1e-9)

# ---- dates ----
def test_age_nearest_basic():
    assert H.age_nearest(date(1971, 1, 1), ASOF) == 56
    assert H.age_nearest(date(1969, 3, 28), date(2026, 12, 31)) == 58
def test_attained_age(): assert H.attained_age(date(1969, 3, 28), date(2027, 3, 27)) == 57
def test_attained_age_before_dob():
    with pytest.raises(ValueError): H.attained_age(date(2000, 1, 1), date(1999, 1, 1))
def test_work_incur():
    assert H.work_incur(2028, date(2029, 3, 28)) == 1.0
    assert H.work_incur(2030, date(2029, 3, 28)) == 0.0
    assert H.work_incur(2029, date(2029, 3, 28)) == pytest.approx(86 / 365)
def test_proj_length(): assert H.proj_length(120, [date(1969, 3, 28), date(1971, 1, 1)], ASOF) == 64

# ---- mortgage ----
def test_mortgage_amortizes():
    pmt = H.monthly_payment(150000, 0.03, 60)
    assert pmt == pytest.approx(2695.3035996095236, abs=1e-6)  # Projection!BQ5
    assert H.mtg_bal_eoy(150000, 0.03, pmt, 5) == pytest.approx(0, abs=1e-6)
    assert H.mtg_bal_eoy(150000, 0.03, pmt, 6) == 0
    assert H.mtg_bal_eoy(1200, 0.0, 100, 0.5) == pytest.approx(600)

# ---- draws, survivorship combinators ----
def test_pretax_draw():
    assert H.pretax_draw(10000, 100000, 0.06, 1) == 6000
    assert H.pretax_draw(5000, 100000, 0.06, 1) == 5000
    assert H.pretax_draw(10000, 100000, 0.06, 0) == 0
    assert H.pretax_draw(-5, 100000, 0.06, 1) == 0
def test_frasier():
    px, py = np.array([.9, .8]), np.array([.5, .5])
    assert H.frasier(px, py, "joint") == pytest.approx([.45, .4])
    assert H.frasier(px, py, " Last Survivor ") == pytest.approx([.95, .9])
    with pytest.raises(ValueError): H.frasier(px, py, "bogus")
def test_time_factor(): assert (H.time_factor("Monthly"), H.time_factor("Yearly")) == (12, 1)

# ---- RMD ----
def test_rmd_start_ages():
    f = {73: 26.5, 75: 24.6}
    assert H.rmd(date(1955, 1, 1), 2027, 265000, f) == 0
    assert H.rmd(date(1955, 1, 1), 2028, 265000, f) == pytest.approx(10000)
    assert H.rmd(date(1965, 1, 1), 2039, 246000, f) == 0
    assert H.rmd(date(1965, 1, 1), 2040, 246000, f) == pytest.approx(10000)
    assert H.rmd(date(1900, 1, 1), 2020, 100, {}) == pytest.approx(50)
    with pytest.raises(KeyError): H.rmd(date(1955, 1, 1), 2028, 1000, {})

# ---- tax / IRA / Roth ----
def test_tax_zero_below_deduction(tax): assert T.tax_est(tax, 20000, 0, True, 0, 0) == 0
def test_tax_first_bracket_only(tax): assert T.tax_est(tax, 32200 + 10000, 0, True, 0, 0) == pytest.approx(1000)
def test_tax_ltcg_zero_rate(tax): assert T.tax_est(tax, 0, 50000, True, 0, 0) == 0
def test_tax_niit(tax): assert T.tax_est(tax, 300000, 100000, True, 0, 0) > T.tax_est(tax, 300000, 0, True, 0, 0) + 100000 * 0.15
def test_ira_fill(tax):
    assert T.ira_fill(tax, 0, 0, True, 0, 0, 1e9, 2) == pytest.approx(100800 + 32200)
    assert T.ira_fill(tax, 0, 0, True, 0, 0, 50000, 2) == 50000
    assert T.ira_fill(tax, 999999, 0, True, 0, 0, 1e9, 2) == 0
def test_roth_limit():
    assert T.roth_limit(100000, True, 58, 56, 0, 0.03) == 2 * (7500 + 1100)
    assert T.roth_limit(300000, True, 58, 56) == 0
    assert T.roth_limit(5000, False, 40, 40) == 5000
    assert T.roth_limit(100000, True, 30, 30) == 15000
def test_forecast_ssi():
    v = T.forecast_ssi([65, 66, 67, 68], [1.02] * 4, 67, 3050, "Monthly")
    assert v[:2].tolist() == [0, 0] and v[2] == pytest.approx(3050 * 12 * 1.02 ** 2)

# ---- mortality ----
def test_blank_qx_raises_by_default(mort):
    with pytest.raises(ValueError): M.tpx_curve(mort, "RP-2014ME", 0, 5)
def test_rp_survivorship_matches_projection_I(mort, ref):
    """Excel passes ASOFDATE() (= t_ret_date when PRERET) to PROJECTMORTALITY_RP."""
    asof = date(2029, 3, 28)
    s = M.project_mortality_rp(mort, 64, "last_survivor", True, "RP-2014", date(1969, 3, 28), date(1971, 1, 1),
                               "M", False, asof, asof)
    assert len(s) == 64 and np.abs(s - ref["I"].to_numpy(float)).max() < 1e-12

# ---- curves & scenarios ----
def test_curve_parity_with_workbook_table():
    dr = rd("tblDiscountRates")
    c = DiscountCurve.from_df(rd("TreasuryCurve"), "legacy")
    for y in (1, 2, 30, 64):
        assert c.rate(y) == pytest.approx(dr.ExpenseDiscountRt[y - 1], abs=1e-12)
    tbl = DiscountCurve("tbl", tuple(dr.Year.astype(float)), tuple(dr.ExpenseDiscountRt))
    for y in (1, 2, 64): assert tbl.disc(y, "MID") == pytest.approx(dr.ExpDiscFact[y - 1], rel=1e-9)
    assert c.with_spread(0.015).rate(1) == pytest.approx(dr.EmploymentDiscountRt[0], abs=1e-12)
def test_curve_is_regression_not_interpolation():
    c = DiscountCurve("x", (1, 2, 3), (0.01, 0.05, 0.02))
    assert c.rate(2) != pytest.approx(0.05)
    assert DiscountCurve("y", (1, 2, 3), (0.01, 0.05, 0.02), method="interp_linear").rate(2) == pytest.approx(0.05)
def test_curve_validation():
    with pytest.raises(ValueError): DiscountCurve("bad", (1,), (0.01,))
def test_inflation_scenario():
    s = inflation_scenario.from_legacy_table(rd("tblInflation"), "CPI70", "COLA70")
    assert s.expense_factors(0.025, 3)[0] == pytest.approx(1 + 0.057 + 0.025)
    assert s.cola_factors(64)[-1] == pytest.approx(1.0252)
    with pytest.raises(ValueError): s.cola_factors(65)
    with pytest.raises(ValueError): inflation_scenario("pct", (5.7,), (3.0,))
    assert inflation_scenario.constant(0.02).shifted(100).cpi[0] == pytest.approx(0.03)

# ---- inputs ----
def test_input_defaults():
    i = ProjectionInputs()
    assert i.joint and i.discount_rate == pytest.approx(0.952380952380952)
    assert ProjectionInputs(spouse_dob=None).joint is False
def test_input_validation():
    with pytest.raises(ValueError): ProjectionInputs(ssi_claim_age=55)
    with pytest.raises(ValueError): ProjectionInputs(primary_target_ret_date=date(1960, 1, 1))
    with pytest.raises(ValueError): ProjectionInputs(bogus=1)

# ---- column-level parity against cached Projection values ----
def test_parity_inflation_cola_columns(ref):
    s = inflation_scenario.from_legacy_table(rd("tblInflation"), "CPI70", "COLA70")
    assert np.allclose(s.expense_factors(0.025, 64), ref["E"], rtol=0, atol=1e-12)
    assert np.allclose(s.cola_factors(64), ref["Q"], rtol=0, atol=1e-12)
def test_parity_ssi_column_V(ref):
    s = inflation_scenario.from_legacy_table(rd("tblInflation"), "CPI70", "COLA70")
    v = T.forecast_ssi(ref["C"], s.cola_factors(64), 67, 3050, "Monthly")
    assert np.allclose(v, ref["V"].astype(float), atol=0.01)
def test_parity_work_fraction_AG(ref):
    ag = [H.work_incur(int(y), date(2029, 3, 28)) for y in ref["B"]]
    assert np.allclose(ag, ref["AG"].astype(float), atol=1e-12)
def test_parity_mortgage_BP(ref):
    pmt = H.monthly_payment(150000, 0.03, 60)
    bp = [H.mtg_bal_eoy(150000, 0.03, pmt, int(a)) for a in ref["A"]]
    assert np.allclose(bp, ref["BP"].astype(float), atol=0.01)
def test_parity_ages_C_D(ref):
    c = [H.age_nearest(date(1969, 3, 28), date(int(y), 12, 31)) for y in ref["B"]]
    d = [H.age_nearest(date(1971, 1, 1), date(int(y), 12, 31)) for y in ref["B"]]
    assert c == ref["C"].astype(int).tolist() and d == ref["D"].astype(int).tolist()
def test_parity_flat_discount_J(ref):
    j = ProjectionInputs().discount_rate ** ref["A"].astype(float)
    assert np.allclose(j, ref["J"].astype(float), atol=1e-12)
