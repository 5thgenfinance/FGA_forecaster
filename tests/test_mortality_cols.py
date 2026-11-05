"""Fails until scripts/patch_mortality_iam.py (or the manual edit) has added _cols to model/mortality.py."""
from model.mortality import _cols

def test_rp_unchanged():
    assert _cols("RP-2014", "M", "H") == ("RP-2014ME", "RP-2014MH")
    assert _cols("RP-2014", "F", "D") == ("RP-2014FE", "RP-2014FD")

def test_iam_single_column():
    assert _cols("IAM2012", "M", "H") == ("IAM2012M", "IAM2012M")
    assert _cols("IAM2012", "F", "H") == ("IAM2012F", "IAM2012F")
    assert _cols("IAM 2012", "M", "D") == ("IAM2012M", "IAM2012M")     # space tolerated (old client files)
