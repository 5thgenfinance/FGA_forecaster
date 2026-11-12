"""Fifth Generation Advisers brand tokens, CSS and chart template."""
from __future__ import annotations
import base64, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND = json.loads((ROOT / "brand" / "fga_brand.json").read_text(encoding="utf8"))
C = BRAND["colors"]
NAVY, BRONZE, OFFWHITE, CHARCOAL = C["navy"], C["bronze"], C["offwhite"], C["charcoal"]
HEAD, BODY = BRAND["fonts"]["heading"], BRAND["fonts"]["body"]
# Tints of the palette for multi-series charts (brand colours first, then tints).
SERIES = [NAVY, BRONZE, "#5b6a8c", "#d4b472", "#9aa5bd", "#9f7233", "#c9cfdd", "#e5e0d8"]
FONT_URL = ("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700"
            "&family=Source+Sans+3:wght@400;600&display=swap")


def logo_path(kind: str = "ribbon", dark_surface: bool = False) -> Path:
    key = f"{kind}_{'dark' if dark_surface else 'light'}"
    return ROOT / BRAND["logos"][key]


def logo_data_uri(kind: str = "ribbon", dark_surface: bool = False) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(logo_path(kind, dark_surface).read_bytes()).decode()


def web_css() -> str:
    return f"""@import url('{FONT_URL}');
html, body, [class*="css"], .stApp {{ font-family:'{BODY}',sans-serif; color:{CHARCOAL}; background:{OFFWHITE}; }}
h1,h2,h3 {{ font-family:'{HEAD}',serif !important; color:{NAVY}; }}
h1 {{ font-weight:700; }} h2,h3 {{ font-weight:400; }}
hr {{ border:0; border-top:1px solid {BRONZE}; }}
[data-testid="stSidebar"] {{ background:#ffffff; border-right:1px solid {BRONZE}; }}
[data-testid="stMetricValue"] {{ font-family:'{HEAD}',serif; color:{NAVY}; }}
.stButton>button, .stDownloadButton>button {{ background:{NAVY}; color:{OFFWHITE}; border:1px solid {NAVY}; }}
.stButton>button:hover, .stDownloadButton>button:hover {{ border-color:{BRONZE}; color:{BRONZE}; }}
"""


def report_css() -> str:
    return web_css() + f"""
.fga-header {{ background:{NAVY}; padding:16px 24px; border-bottom:3px solid {BRONZE}; }}
.fga-header img {{ height:64px; }}
.fga-footer {{ font-size:13px; border-top:1px solid {BRONZE}; margin-top:32px; padding-top:16px; }}
"""


def plotly_layout() -> dict:
    return dict(font=dict(family=f"{BODY}, sans-serif", color=CHARCOAL),
                title=dict(font=dict(family=f"{HEAD}, serif", color=NAVY)),
                paper_bgcolor=OFFWHITE, plot_bgcolor="#ffffff", colorway=SERIES)


def apply_to_figure(fig):
    fig.update_layout(**plotly_layout())
    return fig


def report_brand():
    # Brand for the HTML/PDF report and charts, built from the same tokens as the app.
    from .dashboard import Brand

    return Brand(
        firm_name=BRAND.get("firm_name", "Fifth Generation Advisers"),
        tagline=BRAND.get("tagline", "Registered Investment Adviser"),
        report_title="Retirement Forecast",
        primary=NAVY, accent=BRONZE, light=OFFWHITE,
        font=f"'{BODY}', Helvetica, Arial, sans-serif",
        palette=tuple(SERIES[:6]) + ("#C0392B",),   # 7 entries; index 6 = income taxes (red)
    )
