"""Codemod: rename input identifiers to the new naming standard across the repository.
The mapping is read from model/input_names.json.

    python tools/rename_inputs.py               # dry run: prints what would change, edits nothing
    python tools/rename_inputs.py --apply       # edit files (needs a clean git tree unless --force)

What it changes (using Python's parser, so comments and prose are left alone):
  * variable / attribute / argument names that exactly equal an old input name
  * keyword arguments (except on Streamlit widget calls, e.g. st.checkbox(disabled=...))
  * string literals that exactly equal an old name (dict keys, lists, session keys, ...), except in files whose name
    contains parity / export / workbook, because those strings may be Excel defined names. Those are listed for review.
  * JSON files under tests/ whose "inputs" use old keys.
Requires Python 3.12+ (exact positions inside f-strings).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING_FILE = ROOT / "model" / "input_names.json"
SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", "node_modules", "data_user", "build", "dist"}
SKIP_FILES = {"rename_inputs.py", "legacy_names.py", "test_legacy_names.py", "test_naming_post_refactor.py"}
STRING_REVIEW_FRAGMENTS = ("parity", "export", "workbook")
ST_CALL = re.compile(r"^(st|streamlit)\.|\.(checkbox|button|text_input|number_input|date_input|selectbox|slider|"
                     r"select_slider|radio|toggle|download_button|file_uploader|multiselect|text_area|form_submit_button)$")


def load_mapping(path: Path = MAPPING_FILE) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf8"))
    if len(set(data.values())) != len(data):
        raise SystemExit("input_names.json: two old names map to the same new name")
    if set(data) & set(data.values()):
        raise SystemExit("input_names.json: a new name is also an old name (rename chains are not supported)")
    return data


def py_files(root: Path):
    for p in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in p.parts) or p.name in SKIP_FILES:
            continue
        yield p


def analyse(path: Path, mapping: dict[str, str]):
    """Return (new_source_bytes | None, stats, review_lines, existing_new_identifiers)."""
    src = path.read_bytes()
    tree = ast.parse(src, filename=str(path))
    starts = [0]
    for line in src.split(b"\n"):
        starts.append(starts[-1] + len(line) + 1)
    pos = lambda lineno, col: starts[lineno - 1] + col  # noqa: E731

    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node
    in_fstring = {id(c) for n in ast.walk(tree) if isinstance(n, ast.JoinedStr) for c in ast.walk(n) if c is not n}

    review_strings = any(f in path.name.lower() for f in STRING_REVIEW_FRAGMENTS)
    edits, review, stats, mismatches = [], [], {"names": 0, "strings": 0, "skipped_kw": 0}, []
    new_names = set(mapping.values())
    existing_new = set()

    def add(start, end, expected: bytes, new: bytes, kind: str, lineno: int):
        if src[start:end] != expected:
            mismatches.append(f"{path.name}:{lineno} position mismatch for {expected.decode()}")
            return
        edits.append((start, end, new))
        stats[kind] += 1

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in new_names:
                existing_new.add(node.id)
            if node.id in mapping:
                s = pos(node.lineno, node.col_offset)
                add(s, s + len(node.id.encode()), node.id.encode(), mapping[node.id].encode(), "names", node.lineno)
        elif isinstance(node, ast.Attribute):
            if node.attr in new_names:
                existing_new.add(node.attr)
            if node.attr in mapping:
                e = pos(node.end_lineno, node.end_col_offset)
                n = len(node.attr.encode())
                add(e - n, e, node.attr.encode(), mapping[node.attr].encode(), "names", node.end_lineno)
        elif isinstance(node, ast.arg):
            if node.arg in new_names:
                existing_new.add(node.arg)
            if node.arg in mapping:
                s = pos(node.lineno, node.col_offset)
                add(s, s + len(node.arg.encode()), node.arg.encode(), mapping[node.arg].encode(), "names", node.lineno)
        elif isinstance(node, ast.keyword) and node.arg:
            if node.arg in new_names:
                existing_new.add(node.arg)
            if node.arg in mapping:
                call = parent.get(node)
                callee = ast.unparse(call.func) if isinstance(call, ast.Call) else ""
                if ST_CALL.search(callee):
                    stats["skipped_kw"] += 1
                    review.append(f"{path.name}:{node.lineno} keyword {node.arg}= left unchanged on {callee}(...)")
                    continue
                s = pos(node.lineno, node.col_offset)
                add(s, s + len(node.arg.encode()), node.arg.encode(), mapping[node.arg].encode(), "names", node.lineno)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in mapping:
            if id(node) in in_fstring or isinstance(parent.get(node), ast.Expr):
                continue
            if review_strings:
                review.append(f"{path.name}:{node.lineno} string {node.value!r} not changed (file may use Excel names)")
                continue
            s, e = pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset)
            seg = src[s:e]
            if re.fullmatch(rb"[rRuU]?([\'\"])" + re.escape(node.value.encode()) + rb"\1", seg):
                add(s, e, seg, seg.replace(node.value.encode(), mapping[node.value].encode(), 1), "strings", node.lineno)

    if mismatches:
        review.extend(mismatches)
    if not edits:
        return None, stats, review, existing_new
    out = src
    for s, e, new in sorted(edits, key=lambda x: -x[0]):
        out = out[:s] + new + out[e:]
    return out, stats, review, existing_new


def migrate_json(root: Path, mapping: dict[str, str], apply: bool):
    changed = []
    for p in sorted((root / "tests").rglob("*.json")) if (root / "tests").exists() else []:
        try:
            data = json.loads(p.read_text(encoding="utf8"))
        except (OSError, ValueError):
            continue
        target = data.get("inputs") if isinstance(data, dict) and isinstance(data.get("inputs"), dict) else None
        if target is None and isinstance(data, dict) and sum(k in mapping for k in data) >= 3:
            target = data
        if target is None or not any(k in mapping for k in target):
            continue
        renamed = {mapping.get(k, k): v for k, v in target.items()}
        if target is data:
            data = renamed
        else:
            data["inputs"] = renamed
        changed.append(p)
        if apply:
            p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf8")
    return changed


def git_clean(root: Path) -> bool | None:
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip() == ""
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    ap.add_argument("--force", action="store_true", help="allow --apply with uncommitted changes")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()
    if sys.version_info < (3, 12):
        print("Python 3.12 or newer is required."); return 2
    root = Path(args.root).resolve()
    mapping = load_mapping(root / "model" / "input_names.json")

    if args.apply and not args.force:
        clean = git_clean(root)
        if clean is False:
            print("Uncommitted changes found. Commit (or stash) first so the rename is a separate, reviewable commit,\n"
                  "or re-run with --force."); return 2
        if clean is None:
            print("Note: git not available; make your own backup before continuing.")

    results, all_review, all_existing, originals = [], [], set(), {}
    for p in py_files(root):
        try:
            new, stats, review, existing = analyse(p, mapping)
        except SyntaxError as e:
            all_review.append(f"{p.relative_to(root)}: could not parse ({e.msg}) - skipped")
            continue
        all_existing |= existing
        all_review += [f"{p.relative_to(root)}: {r}" if not r.startswith(p.name) else r for r in review]
        if new is not None:
            results.append((p, new, stats))
            originals[p] = p.read_bytes()

    print(f"{'APPLY' if args.apply else 'DRY RUN'}: {len(results)} Python file(s) would change")
    for p, _, st in results:
        print(f"  {p.relative_to(root)}: {st['names']} name(s), {st['strings']} string(s)")
    json_changed = migrate_json(root, mapping, args.apply)
    for p in json_changed:
        print(f"  {p.relative_to(root)}: JSON inputs migrated")
    if all_existing:
        print("\nWARNING: these new names already exist in the code (possible clash): " + ", ".join(sorted(all_existing)))
    if all_review:
        print("\nReview these:")
        for r in all_review:
            print("  - " + r)

    if not args.apply:
        print("\nNothing was changed. Re-run with --apply when the list above looks right."); return 0

    for p, new, _ in results:
        p.write_bytes(new)
    bad = []
    for p, _, _ in results:
        try:
            py_compile.compile(str(p), doraise=True)
        except py_compile.PyCompileError as e:
            bad.append((p, e))
    if bad:
        for p, e in bad:
            print(f"Syntax error after rename in {p}: {e}")
        for p, orig in originals.items():
            p.write_bytes(orig)
        print("All Python edits were rolled back (JSON files, if any, were already migrated).")
        return 1
    print("\nDone. Next: run pytest (golden and rule tests must give identical numbers), then review `git diff`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
