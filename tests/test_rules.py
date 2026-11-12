"""Rule tests: properties that must hold whatever the exact numbers are. They do not depend on Excel."""
import numpy as np
import pytest

try:
    from tests._golden_support import run
except ImportError:
    from _golden_support import run

pytestmark = pytest.mark.rules

SINGLE = {"spouse_dob": None, "spouse_target_ret_date": None}


def test_survivorship_is_a_probability_that_never_rises():
    i = run().df["I"].dropna().to_numpy(dtype=float)
    assert (i >= 0).all() and (i <= 1 + 1e-12).all()
    assert (np.diff(i) <= 1e-12).all()


def test_couple_last_survivor_at_least_as_likely_as_primary_alone():
    couple = run().df["I"].dropna().to_numpy(dtype=float)
    single = run(SINGLE).df["I"].dropna().to_numpy(dtype=float)
    n = min(len(couple), len(single))
    assert (couple[:n] >= single[:n] - 1e-12).all()


def test_higher_expenses_raise_the_reserve_and_lower_the_surplus():
    base, more = run(), run({"net_expenses": 5000 * 1.10})
    assert more.df["P"].iloc[0] > base.df["P"].iloc[0]
    assert more.kpis["surplus"] < base.kpis["surplus"]


def test_lower_expenses_do_the_opposite():
    base, less = run(), run({"net_expenses": 5000 * 0.95})
    assert less.df["P"].iloc[0] < base.df["P"].iloc[0]
    assert less.kpis["surplus"] > base.kpis["surplus"]


def test_single_plan_ignores_spouse_inputs():
    a = run(SINGLE).kpis
    b = run({**SINGLE, "spouse_trad_ira": 0.0}).kpis
    assert dict(a) == dict(b)
