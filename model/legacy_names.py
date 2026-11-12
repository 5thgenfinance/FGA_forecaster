"""Old (workbook-era) input names <-> new standard names. The mapping lives in model/input_names.json.

Naming standard: snake_case; primary_/spouse_/sleeve3_ prefixes; unit suffixes (_date, _age, _freq, _rate, _months,
_balance). Workbook defined names still use the OLD names, so use OLD_TO_NEW when reading from the workbook and when
loading client files saved before the rename. Edit the JSON, then run tools/rename_inputs.py.
"""
from __future__ import annotations

import json
from pathlib import Path

MAPPING_FILE = Path(__file__).with_name("input_names.json")


def load_mapping(path: Path = MAPPING_FILE) -> dict[str, str]:
    data = json.loads(Path(path).read_text(encoding="utf8"))
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError(f"{path.name} must be a flat JSON object of old name -> new name (strings)")
    if len(set(data.values())) != len(data):
        raise ValueError(f"{path.name}: two old names map to the same new name")
    return data


OLD_TO_NEW: dict[str, str] = load_mapping()
NEW_TO_OLD: dict[str, str] = {v: k for k, v in OLD_TO_NEW.items()}
EXCEL_NAME_TO_NEW = OLD_TO_NEW      # workbook defined names keep the old spelling


def migrate_inputs(data: dict) -> dict:
    """Rename old keys to the new standard. Unknown keys are kept; already-new keys pass through (idempotent)."""
    return {OLD_TO_NEW.get(k, k): v for k, v in data.items()}


def to_legacy_inputs(data: dict) -> dict:
    """Inverse of migrate_inputs: for writing files the old app version can read, or matching workbook names."""
    return {NEW_TO_OLD.get(k, k): v for k, v in data.items()}
