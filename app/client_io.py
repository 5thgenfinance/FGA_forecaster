"""Client file export/import (JSON). Streamlit-independent so it can be unit-tested."""
from __future__ import annotations
import json, re
from dataclasses import dataclass, field
from datetime import date, datetime
from pydantic import ValidationError
from model.inputs import ProjectionInputs

SCHEMA = "fga-client-v1"


@dataclass
class ImportResult:
    inputs: ProjectionInputs | None = None
    client_name: str = ""
    valuation_date: date | None = None
    errors: list[str] = field(default_factory=list)


def clean_name(name: object) -> str:
    return str(name or "").strip()[:200]


def file_name(client_name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", clean_name(client_name)).strip("_")
    return f"{slug or 'client'}_inputs.json"


def build_export(inputs: ProjectionInputs, client_name: str, valuation_date: date) -> str:
    doc = {"schema": SCHEMA,
           "exported_at": datetime.now().isoformat(timespec="seconds"),
           "client_name": clean_name(client_name),
           "valuation_date": valuation_date.isoformat(),
           "inputs": inputs.model_dump(mode="json")}
    return json.dumps(doc, indent=2)


def parse_import(text: str | bytes) -> ImportResult:
    res = ImportResult()
    try:
        doc = json.loads(text)
    except (ValueError, TypeError) as e:
        res.errors.append(f"Not a valid JSON file ({e}).")
        return res
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        res.errors.append(f"Not a client file from this app (expected schema '{SCHEMA}').")
        return res
    if not isinstance(doc.get("inputs"), dict):
        res.errors.append("The file has no 'inputs' section.")
        return res
    res.client_name = clean_name(doc.get("client_name"))
    try:
        res.valuation_date = date.fromisoformat(doc["valuation_date"]) if doc.get("valuation_date") else None
    except ValueError:
        res.valuation_date = None
    try:
        res.inputs = ProjectionInputs(**doc["inputs"])
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"]) or "inputs"
            res.errors.append(f"{loc}: {err['msg']}")
    except TypeError as e:
        res.errors.append(str(e))
    return res
