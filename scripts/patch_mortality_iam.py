"""Adds the non-RP (IAM2012) column logic to model/mortality.py.  Usage:  python scripts/patch_mortality_iam.py
Backs up the file to mortality.py.bak, is safe to run twice, and stops without writing if it cannot find the lines it expects."""
import re, shutil, sys
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "model" / "mortality.py"
HELPER = """def _cols(prefix: str, sex: str, phase: str) -> tuple[str, str]:
    \"\"\"(pre-retirement column, post-retirement column). Non-RP tables have one column for both.\"\"\"
    p = prefix.replace(" ", "")              # tolerate "IAM 2012" in old client files
    if p.upper().startswith("RP"):
        return f"{p}{sex}E", f"{p}{sex}{phase}"
    c = f"{p}{sex}"
    return c, c


"""
PATTERN = re.compile(r'f"\{prefix\}\{(\w+)\}E",\s*f"\{prefix\}\{\1\}(?:\{(\w+)\}|([A-Z]))"')


def patch(src: str) -> tuple[str, int]:
    if "def _cols(" in src:
        return src, -1
    def repl(m):
        phase = m.group(2) if m.group(2) else '"' + m.group(3) + '"'
        return f"*_cols(prefix, {m.group(1)}, {phase})"
    new, n = PATTERN.subn(repl, src)
    if n == 0:
        return src, 0
    m = re.search(r"^def project_mortality_rp", new, re.M)
    if not m:
        return src, 0
    return new[:m.start()] + HELPER + new[m.start():], n


def main() -> int:
    src = PATH.read_text(encoding="utf8")
    new, n = patch(src)
    if n == -1:
        print("Already patched (_cols exists). Nothing to do."); return 0
    if n == 0:
        print("Could not find the RP column-name lines to replace. No changes written. Apply the manual edit instead."); return 1
    shutil.copy(PATH, PATH.with_suffix(".py.bak"))
    PATH.write_text(new, encoding="utf8")
    print(f"Patched {n} call(s) in {PATH.name}; backup saved as {PATH.name}.bak"); return 0


if __name__ == "__main__":
    sys.exit(main())
