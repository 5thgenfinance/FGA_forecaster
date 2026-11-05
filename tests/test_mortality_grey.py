from app.mortality_options import DEFAULT, UNAVAILABLE, MARKER, effective, option_label

def test_labels_and_fallback():
    assert option_label("RP-2014") == "RP-2014"
    assert option_label("IAM2012") == f"IAM2012 {MARKER}"
    assert effective("IAM2012") == DEFAULT and effective("RP-2014") == "RP-2014"
    assert "IAM2012" in UNAVAILABLE

def test_script_builds():
    from app.disabled_options import _JS
    js = _JS % '"(coming soon)"'
    assert "fga-disabled" in js and "(coming soon)" in js
