"""Edits app/ui.py to grey out IAM2012.  Usage:  python scripts/patch_ui_grey_iam.py
Backs up to ui.py.bak, safe to run twice, and writes nothing if it cannot find the expected code."""
import re, shutil, sys
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "app" / "ui.py"
NEW_BRANCH = (
    '{i}elif f == "mort_table":\n'
    '{i}    opts = mortality_options(data_dir(), st.session_state.get("mort_table"))\n'
    '{i}    picked = st.selectbox(LABELS[f], opts, key=f, format_func=option_label,\n'
    '{i}                          index=opts.index(defaults[f]) if defaults[f] in opts else 0)\n'
    '{i}    if picked in UNAVAILABLE:\n'
    '{i}        st.warning(f"{{picked}} is not available yet. Using {{DEFAULT}}.")\n'
    '{i}    side[f] = effective(picked)\n'
)
BRANCH_RE = re.compile(r'^( +)elif f == "mort_table":\n(?:\1 +.*\n)+?(?=\1else:)', re.M)
IMPORT_RE = re.compile(r"^from app\.mortality_options import .*$", re.M)
IMPORT_NEW = ("from app.disabled_options import grey_out_options\n"
              "from app.mortality_options import DEFAULT, UNAVAILABLE, effective, mortality_options, option_label")


def patch(src: str):
    if "grey_out_options" in src:
        return src, "already"
    if not (BRANCH_RE.search(src) and IMPORT_RE.search(src) and "apply_sidebar_theme()\n" in src):
        return src, "missing"
    src = BRANCH_RE.sub(lambda m: NEW_BRANCH.format(i=m.group(1)), src, count=1)
    src = IMPORT_RE.sub(IMPORT_NEW, src, count=1)
    src = src.replace("    apply_sidebar_theme()\n", "    apply_sidebar_theme()\n    grey_out_options()\n", 1)
    return src, "ok"


def main() -> int:
    src = PATH.read_text(encoding="utf8")
    new, status = patch(src)
    if status == "already":
        print("Already patched."); return 0
    if status == "missing":
        print("Could not find the mort_table block / import / apply_sidebar_theme() call. No changes written."); return 1
    shutil.copy(PATH, PATH.with_suffix(".py.bak"))
    PATH.write_text(new, encoding="utf8")
    print("Patched app/ui.py (backup: ui.py.bak)"); return 0


if __name__ == "__main__":
    sys.exit(main())
