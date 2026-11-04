"""Command line: run a projection and write the deliverables.

    python -m app.cli run --inputs inputs.json --as-of 2026-11-03 --out results/ [--data data] [--png] [--pdf]
                          [--brand brand.json] [--client-name "Name"] [--scenarios] [--focus-year 2040] [--offline]

Writes: projection.csv, projection.xlsx, summary.json, report.html and (with --png/--pdf) charts/*.png, report.pdf.
Exit codes: 0 ok | 2 invalid inputs | 3 data/file problem | 4 optional export failed (everything else was written).
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import ValidationError

from model.dashboard import Brand, build_figures, build_report_data
from model.engine import ModelTables
from model.inputs import ProjectionInputs
from model.loop import ForwardTables
from model.report import ENGINE_NOTES, ENGINE_VERSION, assumptions_table, build_html, scenario_table, write_pdf, write_pngs

def format_validation_error(e: ValidationError) -> list[str]:
    """One readable line per problem: 'field: message'."""
    return [f"{'.'.join(str(p) for p in err['loc']) or 'inputs'}: {err['msg']}" for err in e.errors()]

def load_inputs(path: str | None, use_defaults: bool = False) -> ProjectionInputs:
    if use_defaults and not path:
        return ProjectionInputs()
    if not path:
        raise FileNotFoundError("--inputs is required (or pass --use-defaults for the sample household)")
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        import yaml
        raw = yaml.safe_load(text) or {}
    else:
        raw = json.loads(text)
    return ProjectionInputs(**raw)

def _jsonable(o):
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return None if np.isnan(o) else float(o)
    if isinstance(o, (date,)): return o.isoformat()
    if isinstance(o, (np.bool_,)): return bool(o)
    raise TypeError(f"not serializable: {type(o)}")

def write_outputs(rd, figs, out: Path, brand: Brand, client_name: str, offline: bool, png: bool, pdf: bool) -> tuple[list[str], list[str]]:
    """Write all files; returns (files, warnings). Optional exports never prevent the core files being written."""
    out.mkdir(parents=True, exist_ok=True)
    files, warnings = [], []
    rd.df.to_csv(out / "projection.csv", index=False); files.append("projection.csv")
    summary = {"engine_version": ENGINE_VERSION, "summary": rd.summary, "kpis": rd.kpis,
               "assumptions": dict(assumptions_table(rd, rd.summary.get("inflation_id", ""), rd.summary.get("curve_id", ""))),
               "inputs": json.loads(rd.inputs.model_dump_json()), "adviser_notes": ENGINE_NOTES}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=_jsonable), encoding="utf-8"); files.append("summary.json")
    with pd.ExcelWriter(out / "projection.xlsx", engine="openpyxl") as xw:
        rd.df.to_excel(xw, sheet_name="Projection", index=False)
        pd.DataFrame([(k, v) for k, v in rd.kpis.items()], columns=["kpi", "value"]).to_excel(xw, sheet_name="KPIs", index=False)
        pd.DataFrame(list(assumptions_table(rd, rd.summary.get("inflation_id", ""), rd.summary.get("curve_id", ""))),
                     columns=["assumption", "value"]).to_excel(xw, sheet_name="Assumptions", index=False)
    files.append("projection.xlsx")
    (out / "report.html").write_text(build_html(rd, figs, brand, client_name, offline), encoding="utf-8"); files.append("report.html")
    if png or pdf:
        paths, err = write_pngs(figs, out / "charts")
        if err:
            warnings.append(f"PNG/PDF export skipped: {err}. Install kaleido (and Chrome: plotly_get_chrome) to enable it.")
        else:
            files += [f"charts/{p.name}" for p in paths]
            if pdf:
                write_pdf(out / "report.pdf", rd, paths, brand, client_name); files.append("report.pdf")
    return files, warnings

def cmd_run(a) -> int:
    try:
        inputs = load_inputs(a.inputs, a.use_defaults)
    except ValidationError as e:
        print("Invalid inputs:", file=sys.stderr)
        for line in format_validation_error(e): print("  -", line, file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"Cannot read inputs: {e}", file=sys.stderr); return 3
    try:
        as_of = date.fromisoformat(a.as_of) if a.as_of else date.today()
        brand = Brand.from_file(a.brand) if a.brand else Brand()
        tables, ft = ModelTables.from_csv_dir(a.data), ForwardTables.from_csv_dir(a.data)
        rd = build_report_data(inputs, tables, ft, as_of, focus_year=a.focus_year)
        scen = scenario_table(inputs, tables, ft, as_of) if a.scenarios else None
        figs = build_figures(rd, brand, scen)
        files, warnings = write_outputs(rd, figs, Path(a.out), brand, a.client_name or "", a.offline, a.png, a.pdf)
    except (OSError, KeyError, ValueError) as e:
        print(f"Run failed: {type(e).__name__}: {e}", file=sys.stderr); return 3
    k = rd.kpis
    print(f"Funding ratio {k['funding_ratio']:.1%} | surplus/(shortfall) {k['surplus']:,.0f} | scenario {rd.summary['inflation_id']} / {rd.summary['curve_id']}")
    print("Wrote:", ", ".join(files), "->", a.out)
    for w in warnings: print("WARNING:", w, file=sys.stderr)
    return 4 if warnings else 0

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="app.cli", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a projection and write the outputs")
    r.add_argument("--inputs"); r.add_argument("--use-defaults", action="store_true")
    r.add_argument("--as-of", help="valuation date, ISO yyyy-mm-dd (default: today)")
    r.add_argument("--out", default="results"); r.add_argument("--data", default="data")
    r.add_argument("--brand"); r.add_argument("--client-name"); r.add_argument("--focus-year", type=int)
    r.add_argument("--png", action="store_true"); r.add_argument("--pdf", action="store_true")
    r.add_argument("--scenarios", action="store_true", help="add the what-if comparison chart")
    r.add_argument("--offline", action="store_true", help="embed Plotly in the HTML (3 MB) instead of loading it from a CDN")
    return cmd_run(ap.parse_args(argv))

if __name__ == "__main__":
    sys.exit(main())
