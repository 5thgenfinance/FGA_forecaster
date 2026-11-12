"""Put the client name in the report heading:  "<Client name> Retirement Forecast".

    python scripts/patch_report_title.py            # dry run
    python scripts/patch_report_title.py --apply    # edits model/report.py (backup: report.py.bak)

Needs the logo patch (patch_report_logo.py) to be applied first. Safe to re-run.
The heading shows only the report title when no client name is passed.
"""
from __future__ import annotations
import argparse, ast, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHO = '    who = f" for {_e(client_name)}" if client_name else ""\n'
NEW_WHO = WHO + '    title_line = f"{client_name.strip()} {brand.report_title}" if client_name.strip() else brand.report_title\n'
OLD_H1 = '<h1 class="rt">{_e(brand.report_title)}</h1>'
NEW_H1 = '<h1 class="rt">{_e(title_line)}</h1>'


def patch(src: str):
    if "title_line" in src:
        return src, ["already patched"]
    for label, old in (("who line", WHO), ("heading", OLD_H1)):
        n = src.count(old)
        if n != 1:
            return src, [f"{label}: found {n} times (expected 1); nothing written"
                         + ("  (apply patch_report_logo.py first)" if label == "heading" else "")]
    return src.replace(WHO, NEW_WHO, 1).replace(OLD_H1, NEW_H1, 1), ["title_line added", "heading uses title_line"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--file", default=str(ROOT / "model" / "report.py"))
    a = ap.parse_args()
    p = Path(a.file)
    raw = p.read_bytes().decode("utf8")
    crlf = "\r\n" in raw
    src = raw.replace("\r\n", "\n")
    new, notes = patch(src)
    for n in notes:
        print("  - " + n)
    if new == src:
        return 0 if notes == ["already patched"] else 1
    ast.parse(new)
    if not a.apply:
        print("Dry run only. Re-run with --apply.")
        return 0
    Path(str(p) + ".bak").write_bytes(raw.encode("utf8"))
    p.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf8"))
    print("Written (backup .bak).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
