import pandas as pd
from app.mortality_options import available, mortality_options, DEFAULT

def test_available_matches_loosely():
    cols = ["Age", "RP2014_Employee", "RP-2014 Healthy", "IAM2012M", "IAM2012F"]
    assert available(cols) == ["RP-2014"]
    assert available(["Age", "RP-2014MH"]) == ["RP-2014"]
    assert available(["Age"]) == []

def test_options_from_csv_and_fallbacks(tmp_path):
    pd.DataFrame(columns=["Age", "RP-2014ME", "IAM2012M", "IAM2012F"]).to_csv(tmp_path / "tblMortality.csv", index=False)
    assert mortality_options(tmp_path) == ["RP-2014"]
    assert mortality_options(tmp_path, "Custom") == ["RP-2014", "Custom"]
    assert mortality_options(tmp_path / "missing") == [DEFAULT]