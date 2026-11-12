from app.ui_helpers import HELP, INPUT_GROUPS, LABELS
from model.inputs import ProjectionInputs

FIELDS = set(ProjectionInputs.model_fields)

def test_ui_keys_are_model_fields():
    groups = {f for fs in INPUT_GROUPS.values() for f in fs}
    for name, keys in {"HELP": set(HELP), "LABELS": set(LABELS), "INPUT_GROUPS": groups}.items():
        assert keys <= FIELDS, f"{name} has unknown fields: {sorted(keys - FIELDS)}"