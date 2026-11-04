from pathlib import Path
import pandas as pd
import pytest

DATA = Path(__file__).resolve().parents[1] / "data"
EXPECTED = {
    "tblInflation": (64, ["ForecastYr", "CPI_74", "Hist52", "CAGR30", "COLA_74", "CPI70", "COLA70"]),
    "tblLURMD": (49, ["attained_age", "factor"]),
    "tblTax": (6, ["Rate", "Single", "MFJ"]),
    "tblLTGCtax": (3, ["Rate Min", "Single", "MFJ", "Head of household", "MFS"]),
    "tblMortality": (121, ["Age", "IAM2012M", "IAM2012F", "RP-2014ME", "RP-2014FE",
                           "RP-2014MH", "RP-2014FH", "RP-2014MD", "RP-2014FD"]),
    "tblDiscountRates": (64, ["Year", "Hurdle", "ExpenseDiscountRt", "SSIDiscountRt",
                              "EmploymentDiscountRt", "ExpDiscFact", "SSIDiscFact", "EmpDiscFact"]),
    "TreasuryCurve": (8, ["Year", "Name", "Spot Rate", "Maturity"]),
}

@pytest.mark.parametrize("name", EXPECTED)
def test_table_shape(name):
    rows, cols = EXPECTED[name]
    df = pd.read_csv(DATA / f"{name}.csv")
    assert list(df.columns) == cols
    assert len(df) == rows

def test_mortality_ages_complete():
    df = pd.read_csv(DATA / "tblMortality.csv")
    assert df["Age"].tolist() == list(range(0, 121))
    assert df[["IAM2012M", "IAM2012F"]].notna().all().all()

def test_year_keys_sequential():
    assert pd.read_csv(DATA / "tblInflation.csv")["ForecastYr"].tolist() == list(range(1, 65))
    assert pd.read_csv(DATA / "tblDiscountRates.csv")["Year"].tolist() == list(range(1, 65))

def test_treasury_rates_sane():
    df = pd.read_csv(DATA / "TreasuryCurve.csv")
    assert df["Spot Rate"].between(0, 0.15).all()
    assert df["Year"].is_monotonic_increasing
