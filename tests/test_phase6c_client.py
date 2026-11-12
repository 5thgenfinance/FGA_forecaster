import json, pytest
from datetime import date
from app import client_io as C
from model.inputs import ProjectionInputs

def test_roundtrip():
    p = ProjectionInputs(salary=123456, spouse_dob=None, spouse_target_ret_date=None, ret_status="RETIRED", mortality_table="IAM 2012")
    txt = C.build_export(p, "  Pat & Chris  ", date(2026, 11, 4))
    r = C.parse_import(txt)
    assert not r.errors and r.inputs == p and r.client_name == "Pat & Chris" and r.valuation_date == date(2026, 11, 4)

def test_default_roundtrip_has_dates_iso():
    d = json.loads(C.build_export(ProjectionInputs(), "x", date(2026, 11, 4)))
    assert d["schema"] == C.SCHEMA and d["inputs"]["primary_dob"] == "1969-03-28"

@pytest.mark.parametrize("text,msg", [
    ("not json", "valid JSON"), ("[]", "client file"), ('{"schema":"other"}', "client file"),
    ('{"schema":"fga-client-v1"}', "inputs"),
])
def test_bad_files(text, msg):
    r = C.parse_import(text); assert r.inputs is None and msg in r.errors[0]

def test_invalid_values_and_unknown_fields():
    base = json.loads(C.build_export(ProjectionInputs(), "x", date(2026, 11, 4)))
    base["inputs"]["ssi_claim_age"] = 50; base["inputs"]["bogus"] = 1
    r = C.parse_import(json.dumps(base))
    assert r.inputs is None and any("ssi_claim_age" in e for e in r.errors) and any("bogus" in e for e in r.errors)

def test_file_name():
    assert C.file_name("Pat & Chris!") == "Pat_Chris_inputs.json" and C.file_name("") == "client_inputs.json"

def test_groups():
    import importlib, sys, types
    st = types.ModuleType("streamlit"); sys.modules.setdefault("streamlit", st)
    from app import client_details as D
    assert "mortality_table" not in D.CLIENT_FIELDS and list(D.CLIENT_GROUPS) == ["Personal", "Income", "Expenses", "Accounts", "Mortgage"]
    assert D.SIDEBAR_GROUPS["Mortality"] == ["mortality_table"]
    side = [f for fs in D.SIDEBAR_GROUPS.values() for f in fs]
    assert not set(side) & set(D.CLIENT_FIELDS)
    assert set(side) | set(D.CLIENT_FIELDS) == set(f for fs in __import__("app.ui_helpers", fromlist=["x"]).INPUT_GROUPS.values() for f in fs)
    assert list(D.SIDEBAR_GROUPS) == ["Mortality", "Social Security", "Sleeve 3", "Rates", "Scenarios"]
