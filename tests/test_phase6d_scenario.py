from datetime import date
import pytest
from app import scenario as S
from model.inputs import ProjectionInputs

B = ProjectionInputs()

@pytest.mark.parametrize("d,n,exp", [
    (date(2029, 3, 28), 12, date(2030, 3, 28)), (date(2029, 3, 28), -3, date(2028, 12, 28)),
    (date(2029, 1, 31), 1, date(2029, 2, 28)), (date(2028, 1, 31), 1, date(2028, 2, 29)),
    (date(2029, 12, 15), 1, date(2030, 1, 15)), (date(2029, 3, 28), 0, date(2029, 3, 28)),
    (date(2029, 3, 28), -60, date(2024, 3, 28)),
])
def test_add_months(d, n, exp):
    assert S.add_months(d, n) == exp

def test_no_change_gives_no_overrides():
    assert S.build_overrides(B, 0, 0, B.lt_return_rate * 100) == {}
    eff, errs = S.apply_overrides(B, {})
    assert eff is B and errs == []

def test_overrides_and_base_not_mutated():
    o = S.build_overrides(B, 12, -6, 10.0)
    assert o == {"primary_target_ret_date": date(2030, 3, 28), "spouse_target_ret_date": date(2033, 9, 28), "lt_return_rate": 0.10}
    eff, errs = S.apply_overrides(B, o)
    assert not errs and eff.lt_return_rate == 0.10 and eff.primary_target_ret_date == date(2030, 3, 28)
    assert B.lt_return_rate == 0.125 and B.primary_target_ret_date == date(2029, 3, 28)
    assert eff.salary == B.salary and eff.spouse_dob == B.spouse_dob

def test_single_person_ignores_spouse_shift():
    single = ProjectionInputs(spouse_dob=None, spouse_target_ret_date=None)
    assert "spouse_target_ret_date" not in S.build_overrides(single, 0, 24, None)

def test_invalid_override_reported():
    early = ProjectionInputs(primary_dob=date(1990, 1, 1), primary_target_ret_date=date(2030, 1, 1))
    eff, errs = S.apply_overrides(early, {"primary_target_ret_date": date(1989, 1, 1)})
    assert eff is None and errs and "primary_target_ret_date" in errs[0]

def test_return_bounds_keep_no_change_representable():
    assert S.return_bounds(12.5) == (0.0, 15.0)
    assert S.return_bounds(20.0) == (0.0, 20.0) and S.return_bounds(-2.0) == (-2.0, 15.0)
    hi = ProjectionInputs(lt_return_rate=0.20)
    assert S.build_overrides(hi, 0, 0, 20.0) == {}

def test_describe_and_warnings():
    o = S.build_overrides(B, 12, 0, 10.0)
    txt = " ".join(S.describe(B, o))
    assert "Mar 2030" in txt and "10.00%" in txt and "12.50%" in txt
    assert S.warnings(B, date(2026, 11, 4)) == []
    assert S.warnings(B, date(2030, 1, 1))
