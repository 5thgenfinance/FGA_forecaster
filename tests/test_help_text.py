from app.help_text import HELP
from app.ui_helpers import LABELS, PCT_FIELDS

def test_every_input_has_a_tooltip():
    assert set(LABELS) <= set(HELP), sorted(set(LABELS) - set(HELP))
    assert set(HELP) <= set(LABELS), sorted(set(HELP) - set(LABELS))

def test_percent_fields_say_how_to_enter():
    for f in PCT_FIELDS:
        assert "percent" in HELP[f].lower()
