import json
import re
from pathlib import Path

import pytest

from model.legacy_names import MAPPING_FILE, NEW_TO_OLD, OLD_TO_NEW, load_mapping, migrate_inputs, to_legacy_inputs


def test_json_is_a_flat_string_to_string_object():
    data = json.loads(MAPPING_FILE.read_text(encoding="utf8"))
    assert isinstance(data, dict) and data
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in data.items())


def test_mapping_is_one_to_one_without_chains_and_new_names_are_snake_case():
    assert len(NEW_TO_OLD) == len(OLD_TO_NEW)
    assert not (set(OLD_TO_NEW) & set(OLD_TO_NEW.values()))          # a new name is never also an old name
    for new in OLD_TO_NEW.values():
        assert re.fullmatch(r"[a-z][a-z0-9_]*", new), new


def test_duplicate_targets_and_bad_shapes_are_rejected(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"a": "x", "b": "x"}')
    with pytest.raises(ValueError):
        load_mapping(bad)
    bad.write_text('["a", "b"]')
    with pytest.raises(ValueError):
        load_mapping(bad)
    bad.write_text('{"a": 1}')
    with pytest.raises(ValueError):
        load_mapping(bad)


def test_migrate_is_idempotent_and_reversible():
    old = {"p_dob": "1969-03-28", "retired": "PRERET", "LTRoR": 0.125, "something_else": 1}
    new = migrate_inputs(old)
    assert new == {"primary_dob": "1969-03-28", "ret_status": "PRERET", "lt_return_rate": 0.125, "something_else": 1}
    assert migrate_inputs(new) == new
    assert to_legacy_inputs(new) == old
