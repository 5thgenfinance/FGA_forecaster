"""HTML/CSS builders for the header, title and footer (no Streamlit import, so they are unit-testable)."""
from __future__ import annotations
from app.version import version_line

import base64, html
from datetime import date
from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "brand"
PRODUCT = "Fifth Generation Retirement Illustrator"
FIRM = "Fifth Generation Advisers \u00b7 Registered Investment Adviser \u00b7 " + version_line()
DISCLOSURE = "Hypothetical illustration based on stated assumptions; not a guarantee of future results."
NAVY, BRONZE, OFFWHITE, CHARCOAL = "#1a2744", "#c49a4a", "#f7f4ef", "#2c2c2c"
_MIME = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg"}

def asset_path(name: str) -> Path:
    """Prefer vector/transparent files when present: name.svg, then name.png, then name.jpg."""
    for ext in (".svg", ".png", ".jpg"):
        p = ASSETS / f"{name}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"No logo file for '{name}' in {ASSETS}")


def data_uri(name: str) -> str:
    p = asset_path(name)
    return f"data:{_MIME[p.suffix]};base64," + base64.b64encode(p.read_bytes()).decode()


def favicon_path() -> Path:
    return ASSETS / "favicon.png"


def brand_block_html() -> str:
    return (f"<div class='fga-brand'><img src='{data_uri('shield_navy')}' alt='Fifth Generation Advisers'>"
            f"<div><div class='fga-prod'>{html.escape(PRODUCT)}</div>"
            f"<div class='fga-tag'>Registered Investment Adviser</div></div></div>")


def title_html(client_name: str | None, as_of: date) -> str:
    name = html.escape((client_name or "").strip())
    if name:
        kicker, heading, cls = "<div class='fga-kicker'>Prepared for</div>", name, "fga-h1"
    else:
        kicker, heading, cls = "", "Add a client name", "fga-h1 fga-empty"
    return (f"{kicker}<h1 class='{cls}'>{heading}</h1>"
            f"<div class='fga-sub'>Valuation date {as_of:%B} {as_of.day}, {as_of.year}</div>")


def footer_html() -> str:
    return (f"<div class='fga-footer'><img src='{data_uri('shield_cream')}' alt=''>"
            f"<div>{html.escape(DISCLOSURE)}<br><span>{html.escape(FIRM)}</span></div></div>")


_CSS = Template("""
/* Style-only helper blocks (branding, theme, header CSS) must not take up a gap in the page flow */
[data-testid="stElementContainer"]:has(style) { display:none !important; }
[data-testid="stFileUploaderDropzone"] { border:2px dashed $bronze; background:#ffffff; min-height:90px; }
header[data-testid="stHeader"] { background:$navy !important; }
header[data-testid="stHeader"] *, [data-testid="stToolbar"] * { color:#ffffff !important; }
header[data-testid="stHeader"] svg { fill:#ffffff !important; }
.block-container { padding-top:3.75rem !important; padding-left:2rem !important; padding-right:2rem !important; }

/* STICKY: the wrapper around the keyed header container stays pinned under Streamlit's top bar while the page scrolls.
   The wrapper carries the off-white gap below the band so scrolled content cannot show through it. */
div:has(> .st-key-fga_header) { position:sticky; top:3.75rem; z-index:999; background:$offwhite; padding-bottom:10px; }

/* header band: edge to edge, compact, with room so the shield cannot touch the bronze line */
.st-key-fga_header { background:$navy; width:calc(100% + 4rem) !important; max-width:none !important;
                     margin:0 -2rem 0 -2rem; padding:8px 2rem 10px 2rem; border-bottom:3px solid $bronze; box-sizing:border-box; }
.fga-brand { display:flex; align-items:center; gap:12px; position:relative; top:-2px; }
.fga-brand img { height:38px; width:auto; display:block; margin:0; }
.fga-prod { font-family:'Playfair Display',serif; font-weight:700; font-size:24px; line-height:1.1; color:#ffffff; letter-spacing:.03em; }
.fga-tag { font-family:'Source Sans 3',sans-serif; font-size:11px; letter-spacing:.18em; text-transform:uppercase; color:$bronze; margin-top:2px; }
.st-key-fga_header button { background:transparent !important; border:1px solid $bronze !important; }
.st-key-fga_header button svg, .st-key-fga_header button span { color:#ffffff !important; fill:#ffffff !important; }
.st-key-fga_header button[kind="primary"] { background:$bronze !important; }
.st-key-fga_header button[kind="primary"] svg, .st-key-fga_header button[kind="primary"] span { color:$navy !important; fill:$navy !important; }
.fga-kicker { font-family:'Source Sans 3',sans-serif; font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:$bronze; }
.fga-h1 { font-family:'Playfair Display',serif; font-weight:700; color:$navy; margin:0; padding:0 0 4px; border-bottom:2px solid $bronze; display:inline-block; }
.fga-h1 a, .fga-h1 [data-testid="stHeaderActionElements"] { display:none !important; }
.fga-empty { color:#8a93a8 !important; font-weight:400; font-style:italic; border-bottom-color:#d8dce6; }
.fga-sub { color:$charcoal; margin:6px 0 16px; }
.fga-footer { display:flex; align-items:center; gap:14px; border-top:1px solid $bronze; margin-top:32px; padding-top:16px;
              font-size:13px; line-height:1.5; color:$charcoal; }
.fga-footer img { height:40px; width:auto; }
.fga-footer span { color:$navy; font-weight:600; }
""")


def header_css() -> str:
    return _CSS.substitute(navy=NAVY, bronze=BRONZE, charcoal=CHARCOAL, offwhite=OFFWHITE)
