import json
import shutil
from datetime import date
from pathlib import Path
import numpy as np, pandas as pd, pytest
from model.engine import ModelTables
from model.loop import ForwardTables
from model.inputs import ProjectionInputs
from model.pv import run_projection
from model import parity as P
from model.parity import compare_frames, compare_summary, check_invariants, run_case, run_all_cases, discover_cases, write_reports
from model.reference_io import read_inputs, export_case
from model.sweeps import run_sweeps, sweeps_ok, default_sweeps, Sweep

ROOT = Path(__file__).resolve().parents[1]
DATA, CASES = ROOT / "data", ROOT / "reference_cases"
WORKBOOK = ROOT / "reference" / "FGA_Client_Onboarding_Calculator.xlsx"
ASOF = date(2026, 11, 3)

@pytest.fixture(scope="module")
def tables(): return ModelTables.from_csv_dir(DATA)
@pytest.fixture(scope="module")
def ft(): return ForwardTables.from_csv_dir(DATA)
@pytest.fixture(scope="module")
def run(tables, ft): return run_projection(ProjectionInputs(), tables, ft, ASOF, focus_year=2040)
@pytest.fixture(scope="module")
def ref(): return pd.read_csv(CASES / "baseline" / "projection_reference.csv")

# ---- compare_frames ----
def test_baseline_strict_all_columns_pass(run, ref):
    rep = compare_frames(run[0], ref, strict=True)
    assert len(rep) >= 90 and set(rep["status"]) == {"PASS"}

def test_report_has_expected_fields(run, ref):
    rep = compare_frames(run[0], ref)
    assert {"column", "group", "rows", "max_abs_diff", "max_rel_diff", "worst_year", "nan_mismatches", "status"} <= set(rep.columns)
    assert rep.loc[rep["column"] == "BV", "group"].iloc[0] == "Totals"

def test_detects_injected_error(run, ref):
    df = run[0].copy(); df.loc[10, "BV"] += 5.0
    rep = compare_frames(df, ref).set_index("column")
    assert rep.loc["BV", "status"] == "FAIL" and rep.loc["BV", "worst_year"] == 2037
    assert rep.loc["BV", "max_abs_diff"] == pytest.approx(5.0)
    assert (rep.drop("BV")["status"] == "PASS").all()

def test_tolerance_modes(run, ref):
    df = run[0].copy(); df.loc[3, "AO"] += 0.005
    assert compare_frames(df, ref).set_index("column").loc["AO", "status"] == "PASS"
    assert compare_frames(df, ref, strict=True).set_index("column").loc["AO", "status"] == "FAIL"

def test_factor_columns_use_tight_tolerance(run, ref):
    df = run[0].copy(); df.loc[3, "I"] += 1e-6
    assert compare_frames(df, ref).set_index("column").loc["I", "status"] == "FAIL"

def test_nan_pattern_must_match(run, ref):
    df = run[0].copy(); df.loc[5, "DH"] = np.nan
    rep = compare_frames(df, ref).set_index("column")
    assert rep.loc["DH", "status"] == "FAIL" and rep.loc["DH", "nan_mismatches"] == 1

def test_excel_error_cells_treated_as_nan(run, ref):
    assert isinstance(ref["AR"].iloc[-1], str)                      # '#DIV/0!' in the cached workbook
    rep = compare_frames(run[0], ref).set_index("column")
    assert rep.loc["AR", "status"] == "PASS" and rep.loc["AR", "nan_mismatches"] == 0

def test_missing_column_reported(run, ref):
    rep = compare_frames(run[0].drop(columns=["CC"]), ref).set_index("column")
    assert rep.loc["CC", "status"] == "MISSING"

# ---- summary and invariants ----
def test_summary_comparison_passes_and_detects_error(run):
    ref = json.load(open(CASES / "baseline" / "summary_reference.json"))
    assert set(compare_summary(run[1], ref, strict=True)["status"]) == {"PASS"}
    bad = dict(run[1]); bad["act_assets_C1"] += 1.0
    assert compare_summary(bad, ref).set_index("item").loc["C1", "status"] == "FAIL"

def test_invariants_clean_for_baseline(run): assert check_invariants(run[0], run[1]) == []

def test_invariants_detect_corruption(run):
    df = run[0].copy(); df.loc[4, "BV"] += 100
    assert any("BV" in m for m in check_invariants(df))
    df = run[0].copy(); df.loc[4, "AU"] = -50
    assert any("negative balance" in m for m in check_invariants(df))
    df = run[0].copy(); df.loc[2, "I"] = 1.5
    assert any("survivorship" in m for m in check_invariants(df))

# ---- cases ----
def test_case_discovery_and_run(tables, ft):
    assert [p.name for p in discover_cases(CASES)][:1] == ["baseline"]
    res = run_case(CASES / "baseline", tables, ft, strict=True)
    assert res.passed and res.name == "baseline"

def test_changed_inputs_fail_against_baseline_reference(tables, ft, tmp_path):
    """A case whose inputs.json no longer matches the cached values must fail loudly."""
    dst = tmp_path / "bad"; shutil.copytree(CASES / "baseline", dst)
    inp = json.loads((dst / "inputs.json").read_text()); inp["net_expenses"] = 6000
    (dst / "inputs.json").write_text(json.dumps(inp))
    res = run_case(dst, tables, ft)
    assert not res.passed and (res.columns["status"] == "FAIL").any()

def test_write_reports(tables, ft, tmp_path):
    res = run_all_cases(CASES, tables, ft)
    paths = write_reports(res, tmp_path)
    assert (tmp_path / "parity_report.md").exists() and (tmp_path / "baseline_columns.csv").exists()
    assert "baseline: PASS" in (tmp_path / "parity_report.md").read_text() and len(paths) >= 3

# ---- workbook round trip (skipped if the workbook is not in reference/) ----
needs_wb = pytest.mark.skipif(not WORKBOOK.exists(), reason="workbook not in reference/")

@needs_wb
def test_inputs_read_from_workbook_equal_defaults():
    assert read_inputs(WORKBOOK) == ProjectionInputs().model_dump(mode="json")

@needs_wb
def test_export_case_round_trip(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("export_workbook", ROOT / "scripts" / "export_workbook.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    data = tmp_path / "data"; data.mkdir()
    mod.main(str(WORKBOOK), str(data))                       # tables from the SAME workbook state
    export_case(WORKBOOK, tmp_path / "rt", ASOF)
    res = run_case(tmp_path / "rt", ModelTables.from_csv_dir(data), ForwardTables.from_csv_dir(data), strict=True)
    bad_cols = res.columns[res.columns["status"].isin(["FAIL", "MISSING"])]
    bad_sum = res.summary[res.summary["status"] == "FAIL"]
    assert res.passed, f"{bad_cols.to_string()}\n{bad_sum.to_string()}\n{res.invariants}"

# ---- sweeps ----
@pytest.fixture(scope="module")
def sweep_results(tables, ft): return run_sweeps(tables, ft, ASOF)

def test_all_sweeps_pass(sweep_results):
    bad = sweep_results[(sweep_results["invariants"] != "ok") | sweep_results["expectation"].str.startswith(("FAIL", "ERROR"))]
    assert bad.empty, bad[["sweep", "invariants", "expectation"]].to_string()
    assert sweeps_ok(sweep_results) and len(sweep_results) >= 25

def test_sweep_baseline_matches_run(sweep_results, run):
    r = sweep_results.set_index("sweep").loc["baseline"]
    assert r["C1"] == pytest.approx(run[1]["act_assets_C1"]) and r["years"] == 64

def test_known_sweep_relationships(sweep_results):
    r = sweep_results.set_index("sweep")
    assert r.loc["hurdle_3pct", "C2"] == pytest.approx(r.loc["baseline", "C2"])      # hurdle does not touch the liability
    assert r.loc["hurdle_3pct", "C1"] > r.loc["hurdle_8pct", "C1"]
    assert r.loc["ssi_age_62", "C1"] > r.loc["baseline", "C1"] > r.loc["ssi_age_70", "C1"]
    assert r.loc["no_mortgage", "C2"] == pytest.approx(r.loc["baseline", "C2"])      # mortgage is not in the C2 reserve
    assert r.loc["single_person", "C2"] < r.loc["baseline", "C2"]

def test_sweep_failure_is_detected(tables, ft):
    bogus = [Sweep("must_fail", "test", {"net_expenses": 6000}, expect=lambda b, bs, d, s: (False, "forced"))]
    res = run_sweeps(tables, ft, ASOF, bogus)
    assert not sweeps_ok(res) and "forced" in res["expectation"].iloc[0]

def test_sweep_errors_do_not_abort(tables, ft):
    res = run_sweeps(tables, ft, ASOF, [Sweep("bad_inflation", "test", inflation_pair=("NOPE", "COLA70")), Sweep("ok", "test")])
    assert res["expectation"].iloc[0] == "ERROR" and res["invariants"].iloc[1] == "ok"
