import json, re, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
old = json.loads((root / "model/input_names.json").read_text("utf8"))
skip = {"rename_inputs.py", "legacy_names.py", "find_old_names.py",
        "test_legacy_names.py", "test_naming_post_refactor.py"}
pat = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(map(re.escape, old)) + r")(?![A-Za-z0-9_])")
for p in sorted(root.rglob("*.py")):
    if p.name in skip or any(x in p.parts for x in (".venv", ".git", "__pycache__")):
        continue
    for i, line in enumerate(p.read_text("utf8").splitlines(), 1):
        if pat.search(line):
            print(f"{p.relative_to(root)}:{i}: {line.strip()[:110]}")