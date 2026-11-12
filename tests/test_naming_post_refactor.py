"""Fails BEFORE the rename and passes AFTER it: confirms the model really uses the new names."""
import re
from model.inputs import ProjectionInputs
from model.legacy_names import OLD_TO_NEW

def test_model_uses_new_names_only():
    fields = set(ProjectionInputs.model_fields)
    assert not (fields & set(OLD_TO_NEW)), sorted(fields & set(OLD_TO_NEW))
    assert set(OLD_TO_NEW.values()) <= fields, sorted(set(OLD_TO_NEW.values()) - fields)

def test_all_fields_are_snake_case():
    for f in ProjectionInputs.model_fields:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", f), f
