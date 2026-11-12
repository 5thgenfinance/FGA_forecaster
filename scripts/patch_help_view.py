"""Adds a Help view to the app: a ? button in the header that opens the full-page user guide.

    python scripts/patch_help_view.py            # dry run
    python scripts/patch_help_view.py --apply    # edits app/shell.py and app/ui.py (backups: *.bak)

Safe to re-run. If a pattern is not found it says so and changes nothing for that step.
"""
from __future__ import annotations
import argparse, ast, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELP_BTN = (
    '    c3.button("", icon=":material/help:", key="btn_help", help="User guide",\n'
    '              type="primary" if current_view() == "help" else "secondary",\n'
    '              on_click=_go, args=("help" if current_view() != "help" else "forecast",))'
)
HELP_FN = (
    "\n\ndef help_page() -> None:\n"
    "    # Full-page user guide (docs/USER_GUIDE.md).\n"
    "    from app.help_page import render_help_page\n\n"
    '    st.button("Back to forecast", icon=":material/arrow_back:", key="help_back", on_click=_go, args=("forecast",))\n'
    "    render_help_page()\n"
)


def patch_shell(s: str):
    if "def help_page" in s and "btn_help" in s:
        return s, ["shell.py already patched"]
    notes = []
    m = re.search(r'VIEWS\s*=\s*\(([^)]*)\)', s)
    if m and '"help"' not in m.group(1):
        s = s.replace(m.group(0), m.group(0)[:-1].rstrip(", ") + ', "help")', 1); notes.append("VIEWS: added 'help'")
    elif not m:
        notes.append("WARNING: VIEWS tuple not found")
    m = re.search(r'^(\s*)left, c1, c2 = st\.columns\(\[20, 1, 1\](.*)\)[ \t]*$', s, re.M)
    if m:
        new = f"{m.group(1)}left, c1, c2, c3 = st.columns([18, 1, 1, 1]{m.group(2)})"
        s = s.replace(m.group(0), new + "\n" + HELP_BTN, 1); notes.append("header: ? button added")
    else:
        notes.append("WARNING: 'left, c1, c2 = st.columns([20, 1, 1], ...)' not found; button not added")
    if "def help_page" not in s:
        s = s.rstrip("\n") + "\n" + HELP_FN; notes.append("help_page() added")
    return s, notes


def patch_ui(s: str):
    if "help_page" in s:
        return s, ["ui.py already patched"]
    notes = []
    m = re.search(r'^from app\.shell import (.*)$', s, re.M)
    if m:
        s = s.replace(m.group(0), m.group(0).rstrip() + ", help_page", 1); notes.append("import: help_page")
    else:
        notes.append("WARNING: 'from app.shell import ...' not found")
    m = re.search(r'^(\s*)if view == "client": client_page\(\); st\.stop\(\)[ \t]*$', s, re.M)
    if m:
        s = s.replace(m.group(0), m.group(0) + f'\n{m.group(1)}if view == "help": help_page(); st.stop()', 1); notes.append("dispatch: help view")
    else:
        notes.append("WARNING: 'if view == \"client\": client_page(); st.stop()' not found")
    return s, notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args()
    root, rc = Path(a.root), 0
    for rel, fn in (("app/shell.py", patch_shell), ("app/ui.py", patch_ui)):
        p = root / rel
        if not p.exists():
            print(f"{rel}: not found"); rc = 1; continue
        src = p.read_bytes().decode("utf8")
        crlf = "\r\n" in src
        new, notes = fn(src.replace("\r\n", "\n"))
        print(f"{rel}:")
        for n in notes:
            print("  - " + n)
        if any(n.startswith("WARNING") for n in notes):
            rc = 1
        out = new.replace("\n", "\r\n") if crlf else new
        if out == src or not a.apply:
            continue
        try:
            ast.parse(new)
        except SyntaxError as e:
            print(f"  ! result would not parse ({e}); {rel} NOT written"); rc = 1; continue
        Path(str(p) + ".bak").write_bytes(src.encode("utf8"))
        p.write_bytes(out.encode("utf8"))
        print("  written (backup .bak)")
    if not a.apply:
        print("Dry run only. Re-run with --apply.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
