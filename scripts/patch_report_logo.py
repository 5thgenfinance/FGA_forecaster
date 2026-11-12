"""Add a logo header and branded footer to model/report.py (HTML and PDF).

    python scripts/patch_report_logo.py            # dry run
    python scripts/patch_report_logo.py --apply    # edits model/report.py (backup: report.py.bak)

Safe to re-run. If any anchor text is not found exactly once, nothing is written.
After patching, build_html() accepts  logo_uri, shield_uri, footer_note  (default: auto-load from assets/brand/).
"""
from __future__ import annotations
import argparse, ast, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [('import html\nfrom datetime import date', 'import base64\nimport html\nfrom datetime import date'), ('def build_html(rd: ReportData, figs: dict, brand: Brand = Brand(), client_name: str = "", offline: bool = False,\n               inflation_id: str | None = None, curve_id: str | None = None) -> str:', '\nBRAND_DIR = Path(__file__).resolve().parents[1] / "assets" / "brand"\n_MIME = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}\n_FONT_LINK = ("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&"\n              "family=Source+Sans+3:wght@400;600&display=swap")\n\n\ndef find_brand_asset(names, exts=(".svg", ".png", ".jpg", ".jpeg")):\n    """First existing assets/brand/<name><ext>, trying svg, then png, then jpg."""\n    for ext in exts:\n        for n in names:\n            p = BRAND_DIR / f"{n}{ext}"\n            if p.exists():\n                return p\n    return None\n\n\ndef logo_data_uri(path, max_height: int | None = None) -> str:\n    """Embed an image as a data URI (shrunk to max_height pixels when Pillow is available)."""\n    if not path or not Path(path).exists():\n        return ""\n    p = Path(path)\n    raw, mime = p.read_bytes(), _MIME.get(p.suffix.lower(), "application/octet-stream")\n    if max_height and p.suffix.lower() in (".png", ".jpg", ".jpeg"):\n        try:\n            import io\n            from PIL import Image as _PILImage\n\n            im = _PILImage.open(io.BytesIO(raw))\n            if im.height > max_height:\n                im = im.resize((max(1, round(im.width * max_height / im.height)), max_height), _PILImage.LANCZOS)\n                buf = io.BytesIO()\n                if p.suffix.lower() == ".png":\n                    im.save(buf, "PNG", optimize=True)\n                else:\n                    im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True)\n                raw = buf.getvalue()\n        except Exception:\n            pass\n    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"\n\n\ndef _pdf_logo() -> list:\n    """Logo at the top of the PDF (png/jpg only; reportlab cannot draw svg)."""\n    from reportlab.lib.units import inch\n    from reportlab.lib.utils import ImageReader\n    from reportlab.platypus import Image as _RLImage, Spacer as _Spacer\n\n    p = find_brand_asset(("ribbon_navy", "navy_ribbon"), exts=(".png", ".jpg", ".jpeg"))\n    if not p:\n        return []\n    w, h = ImageReader(str(p)).getSize()\n    return [_RLImage(str(p), width=3.2 * inch, height=3.2 * inch * h / w, hAlign="LEFT"), _Spacer(1, 8)]\n\n\ndef build_html(rd: ReportData, figs: dict, brand: Brand = Brand(), client_name: str = "", offline: bool = False,\n               inflation_id: str | None = None, curve_id: str | None = None, logo_uri: str | None = None,\n               shield_uri: str | None = None, footer_note: str = "") -> str:'), ('    return f"""<!DOCTYPE html>', '    if logo_uri is None:\n        logo_uri = logo_data_uri(find_brand_asset(("ribbon_navy", "navy_ribbon")), 116)\n    if shield_uri is None:\n        shield_uri = logo_data_uri(find_brand_asset(("shield_cream", "cream_shield", "cream_shield_tn")), 92)\n    tag = f"<small>{_e(brand.tagline)}</small>" if brand.tagline else ""\n    head_left = (f\'<img class="logo" src="{logo_uri}" alt="{_e(brand.firm_name)}">\' if logo_uri\n                 else f\'<div class="firm">{_e(brand.firm_name)}{tag}</div>\')\n    head_meta = ((f\'<div class="prep">Prepared for</div><div class="who">{_e(client_name)}</div>\' if client_name else "")\n                 + f\'<div class="vd">Valuation date {rd.as_of.isoformat()}</div>\')\n    firm_line = _e(brand.firm_name) + ((" \\u00b7 " + _e(brand.tagline)) if brand.tagline else "")\n    small = " \\u00b7 ".join(x for x in (f"Generated {_e(date.today().isoformat())}", _e(footer_note)) if x)\n    foot_html = (\'<footer class="bf">\' + (f\'<img src="{shield_uri}" alt="">\' if shield_uri else "")\n                 + f\'<div>{_e(SHORT_DISCLAIMER)}<br><b>{firm_line}</b><div class="sm">{small}</div></div></footer>\')\n    return f"""<!DOCTYPE html>'), ('<title>{_e(brand.report_title)}{who} - {_e(brand.firm_name)}</title>\n<style>', '<title>{_e(brand.report_title)}{who} - {_e(brand.firm_name)}</title>\n<link rel="preconnect" href="https://fonts.googleapis.com"><link href="{_FONT_LINK}" rel="stylesheet">\n<style>'), ('body{{font-family:{brand.font};color:#1f2937;margin:0;background:#fff}}\nheader{{background:{brand.primary};color:#fff;padding:28px 40px}}\nheader h1{{margin:0;font-size:28px}} header p{{margin:6px 0 0;opacity:.85}}\n', "body{{font-family:{brand.font};color:#1f2937;margin:0;background:#fff}}\n.bh{{background:{brand.primary};color:#fff;padding:12px 40px;display:flex;align-items:center;justify-content:space-between;gap:24px}}\n.bh .logo{{height:58px;display:block}} .bh .firm{{font-family:'Playfair Display',Georgia,serif;font-size:22px}}\n.bh .firm small{{display:block;font-size:12px;opacity:.85}}\n.bh .meta{{text-align:right}} .bh .prep{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{brand.accent}}}\n.bh .who{{font-family:'Playfair Display',Georgia,serif;font-size:24px;line-height:1.2}} .bh .vd{{font-size:12px;opacity:.85}}\n.brule{{height:3px;background:{brand.accent}}}\nh1.rt{{font-family:'Playfair Display',Georgia,serif;color:{brand.primary};font-size:26px;margin:4px 0 14px}}\nh2{{font-family:'Playfair Display',Georgia,serif}}\nfooter.bf{{display:flex;align-items:center;gap:16px;border-top:2px solid {brand.accent};margin-top:30px;padding:14px 0}}\nfooter.bf img{{height:46px;display:block}} footer.bf b{{color:{brand.primary}}} footer.bf .sm{{font-size:11px;opacity:.9}}\n.bh,.brule,.card,footer.bf{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}\n"), ('<header><h1>{_e(brand.report_title)}{who}</h1><p>{_e(brand.firm_name)}{(" | " + _e(brand.tagline)) if brand.tagline else ""} | Valuation date {rd.as_of.isoformat()}</p></header>\n<main>', '<header class="bh">{head_left}<div class="meta">{head_meta}</div></header><div class="brule"></div>\n<main>\n<h1 class="rt">{_e(brand.report_title)}</h1>'), ('<footer>{_e(SHORT_DISCLAIMER)} Generated {_e(date.today().isoformat())} by {_e(brand.firm_name)}.</footer>', '{foot_html}'), ('    story = [Paragraph(html.escape(brand.report_title', '    story = _pdf_logo() + [Paragraph(html.escape(brand.report_title')]


def patch(src: str):
    if "def logo_data_uri" in src:
        return src, ["already patched"]
    notes, out = [], src
    for i, (old, new) in enumerate(STEPS, 1):
        n = out.count(old)
        if n != 1:
            return src, [f"step {i}: anchor found {n} times (expected 1); nothing written"]
        out = out.replace(old, new, 1)
        notes.append(f"step {i}: ok")
    return out, notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--file", default=str(ROOT / "model" / "report.py"))
    a = ap.parse_args()
    p = Path(a.file)
    src = p.read_bytes().decode("utf8")
    crlf = "\r\n" in src
    norm = src.replace("\r\n", "\n")
    new, notes = patch(norm)
    print(f"{p.name}:")
    for n in notes:
        print("  - " + n)
    if new == norm:
        return 0 if notes == ["already patched"] else 1
    ast.parse(new)
    if not a.apply:
        print("Dry run only. Re-run with --apply.")
        return 0
    Path(str(p) + ".bak").write_bytes(src.encode("utf8"))
    p.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf8"))
    print("Written (backup .bak).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
