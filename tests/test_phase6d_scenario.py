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
    assert S.build_overrides(B, 0, 0, B.LTRoR * 100) == {}
    eff, errs = S.apply_overrides(B, {})
    assert eff is B and errs == []

def test_overrides_and_base_not_mutated():
    o = S.build_overrides(B, 12, -6, 10.0)
    assert o == {"t_ret_date": date(2030, 3, 28), "t_s_ret_date": date(2033, 9, 28), "LTRoR": 0.10}
    eff, errs = S.apply_overrides(B, o)
    assert not errs and eff.LTRoR == 0.10 and eff.t_ret_date == date(2030, 3, 28)
    assert B.LTRoR == 0.125 and B.t_ret_date == date(2029, 3, 28)
    assert eff.salary == B.salary and eff.s_dob == B.s_dob

def test_single_person_ignores_spouse_shift():
    single = ProjectionInputs(s_dob=None, t_s_ret_date=None)
    assert "t_s_ret_date" not in S.build_overrides(single, 0, 24, None)

def test_invalid_override_reported():
    early = ProjectionInputs(p_dob=date(1990, 1, 1), t_ret_date=date(2030, 1, 1))
    eff, errs = S.apply_overrides(early, {"t_ret_date": date(1989, 1, 1)})
    assert eff is None and errs and "t_ret_date" in errs[0]

def test_return_bounds_keep_no_change_representable():
    assert S.return_bounds(12.5) == (0.0, 15.0)
    assert S.return_bounds(20.0) == (0.0, 20.0) and S.return_bounds(-2.0) == (-2.0, 15.0)
    hi = ProjectionInputs(LTRoR=0.20)
    assert S.build_overrides(hi, 0, 0, 20.0) == {}

def test_describe_and_warnings():
    o = S.build_overrides(B, 12, 0, 10.0)
    txt = " ".join(S.describe(B, o))
    assert "Mar 2030" in txt and "10.00%" in txt and "12.50%" in txt
    assert S.warnings(B, date(2026, 11, 4)) == []
    assert S.warnings(B, date(2030, 1, 1))
