"""Golden-master tests: today's Python output for fixed cases must not change unless you decide it should.

First run / after an intended change:
    PowerShell:  $env:UPDATE_GOLDEN=1; pytest -m golden; Remove-Item Env:UPDATE_GOLDEN
    bash:        UPDATE_GOLDEN=1 pytest -m golden
then review `git diff tests/golden/expected` before committing.
These tests do NOT compare against Excel; see the parity tests for that.
"""
import json
import os

import pytest

try:
    from tests._golden_support import AS_OF, GOLDEN_DIR, compare, load_case, run, summarize
except ImportError:  # tests/ is not a package
    from _golden_support import AS_OF, GOLDEN_DIR, compare, load_case, run, summarize

pytestmark = pytest.mark.golden
CASES = sorted((GOLDEN_DIR / "cases").glob("*.json"))


@pytest.mark.parametrize("case_file", CASES, ids=lambda p: p.stem)
def test_golden_case(case_file):
    case = load_case(case_file)
    actual = summarize(run(case.get("inputs", {}), AS_OF))
    expected_file = GOLDEN_DIR / "expected" / case_file.name

    if os.environ.get("UPDATE_GOLDEN"):
        expected_file.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf8")
        pytest.skip(f"golden file written: {expected_file.name}")

    if not expected_file.exists():
        pytest.fail(f"No golden file for '{case_file.stem}'. Create it with UPDATE_GOLDEN=1 pytest -m golden")
    diffs = compare(actual, json.loads(expected_file.read_text(encoding="utf8")))
    assert not diffs, f"{case.get('description', case_file.stem)}\n" + "\n".join(diffs[:25])
