"""Make the report and charts use the FGA brand tokens (brand/fga_brand.json via model/branding.py).

    python scripts/patch_report_brand.py            # dry run
    python scripts/patch_report_brand.py --apply    # edits model/branding.py and app/ui.py (backups: *.bak)

Adds branding.report_brand() -> Brand (navy, bronze, off-white, fonts, chart SERIES palette) and replaces
every  Brand()  in app/ui.py with  report_brand().  Safe to re-run.

The chart palette needs 7 entries: dashboard.py reads palette[0]..palette[4] for series and palette[6] for taxes.
"""
from __future__ import annotations
import argparse, ast, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FUNC = (
    "\n\n"
    "def report_brand():\n"
    "    # Brand for the HTML/PDF report and charts, built from the same tokens as the app.\n"
    "    from .dashboard import Brand\n"
    "\n"
    "    return Brand(\n"
    "        firm_name=BRAND.get(\"firm_name\", \"Fifth Generation Advisers\"),\n"
    "        tagline=BRAND.get(\"tagline\", \"Registered Investment Adviser\"),\n"
    "        report_title=\"Retirement Forecast\",\n"
    "        primary=NAVY, accent=BRONZE, light=OFFWHITE,\n"
    "        font=f\"'{BODY}', Helvetica, Arial, sans-serif\",\n"
    "        palette=tuple(SERIES[:6]) + (\"#C0392B\",),   # 7 entries; index 6 = income taxes (red)\n"
    "    )\n"
)


def patch_branding(src: str):
    if "def report_brand" in src:
        return src, ["branding.py: report_brand() already present"]
    return src.rstrip("\n") + "\n" + FUNC, ["branding.py: added report_brand()"]


def patch_ui(src: str):
    notes, out = [], src
    n = len(re.findall(r"\bBrand\(\)", out))
    if n:
        out = re.sub(r"\bBrand\(\)", "report_brand()", out)
        notes.append(f"ui.py: replaced {n} use(s) of Brand() with report_brand()")
    if "report_brand" in out and not re.search(r"^from model\.branding import .*\breport_brand\b", out, re.M):
        m = re.search(r"^from model\.dashboard import .*$", out, re.M)
        if not m:
            return src, ["ui.py: could not find the 'from model.dashboard import' line; nothing written"]
        out = out.replace(m.group(0), m.group(0) + "\nfrom model.branding import report_brand", 1)
        notes.append("ui.py: added  from model.branding import report_brand")
    return out, notes or ["ui.py: nothing to change"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args()
    root, rc = Path(a.root), 0
    for rel, fn in (("model/branding.py", patch_branding), ("app/ui.py", patch_ui)):
        p = root / rel
        if not p.exists():
            print(f"{rel}: not found"); rc = 1; continue
        raw = p.read_bytes().decode("utf8")
        crlf = "\r\n" in raw
        src = raw.replace("\r\n", "\n")
        new, notes = fn(src)
        for n in notes:
            print("  - " + n)
        if new == src:
            continue
        ast.parse(new)
        if a.apply:
            Path(str(p) + ".bak").write_bytes(raw.encode("utf8"))
            p.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf8"))
            print(f"    written {rel} (backup .bak)")
    if not a.apply:
        print("Dry run only. Re-run with --apply.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
