"""Phase 6 - client report: self-contained HTML (interactive Plotly), PNG charts and a PDF, plus the scenario table."""
from __future__ import annotations
import base64
import html
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .dashboard import Brand, ReportData, fmt_money, fmt_pct, SHORT_DISCLAIMER
from .engine import ModelTables
from .helpers import time_factor
from .inputs import ProjectionInputs
from .loop import ForwardTables
from .pv import run_projection

ENGINE_VERSION = "1.0"

DISCLOSURES = [
    "This report is a hypothetical illustration prepared from the assumptions shown. It is not a guarantee, prediction or "
    "promise of future results, and actual results will differ.",
    "The funding ratio compares the present value of projected resources with the present value of projected lifetime "
    "spending, weighted by the probability that you are alive in each year. It is not a probability of success.",
    "Year-by-year charts are shown in future (nominal) dollars and assume both people are alive in every year shown.",
    "Investment returns, inflation, interest rates, tax law, Social Security rules and life expectancy may differ from the "
    "assumptions. Taxes shown are estimated federal income taxes only; state and local taxes are not modeled.",
    "Social Security benefits are based on the benefit estimate you provided and are not adjusted by this report.",
    "Mortality assumptions use published actuarial tables, not your personal health. This report is not tax, legal or "
    "investment advice. Please review the assumptions with your adviser before relying on any figure.",
]

ENGINE_NOTES = [  # adviser-facing; written to summary.json, not to the client report
    "Shortfall withdrawals from traditional IRAs, brokerage accounts and Sleeve 3 are not included in estimated taxable income.",
    "The hurdle rate affects the asset side (J/K discounting) but not the lifetime-spending liability, which uses the Treasury curve.",
    "The mortgage payments reduce cash flow but the mortgage is not part of the C2 spending reserve.",
    "SSI_PIA is not adjusted for the election age; change it per election age.",
    "Headline Excel parity figures use a 52-year dashboard feed; charts here use the full horizon.",
]

def _e(x) -> str:
    return html.escape(str(x), quote=True)

def assumptions_table(rd: ReportData, inflation_id: str, curve_id: str) -> list[tuple[str, str]]:
    i, k = rd.inputs, rd.kpis
    annual_spend = time_factor(i.expenses_freq) * i.net_expenses
    rows = [
        ("Valuation date", rd.as_of.isoformat()),
        ("Planned retirement", f"{i.primary_target_ret_date.year} (age {k['retirement_age']})"),
        ("Social Security start", f"age {i.ssi_claim_age}; estimated benefit {fmt_money(i.ssi_pia * time_factor(i.ssi_pia_freq), False)} per year in today's dollars"),
        ("Household", "Two people" if i.joint else "One person"),
        ("Planned spending today", f"{fmt_money(annual_spend, False)} per year, plus mortgage payments"),
        ("Inflation assumption", f"{inflation_id} plus {fmt_pct(i.inflation_load, 1)}"),
        ("Return on long-term assets", fmt_pct(i.lt_return_rate, 1)),
        ("Return on 401(k) / cash", fmt_pct(i.growth_rate_401k, 1)),
        ("Sleeve 3 income / growth", f"{fmt_pct(i.sleeve3_income_rate, 1)} / {fmt_pct(i.sleeve3_growth_rate, 1)}"),
        ("Discounting", f"{curve_id}; employment spread {fmt_pct(i.employment_risk_spread, 1)}"),
        ("Mortality table", i.mortality_table),
        ("Taxes", "Estimated federal income tax; standard deduction; brackets indexed to Social Security COLA"),
    ]
    return rows


BRAND_DIR = Path(__file__).resolve().parents[1] / "assets" / "brand"
_MIME = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_FONT_LINK = ("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&"
              "family=Source+Sans+3:wght@400;600&display=swap")


def find_brand_asset(names, exts=(".svg", ".png", ".jpg", ".jpeg")):
    """First existing assets/brand/<name><ext>, trying svg, then png, then jpg."""
    for ext in exts:
        for n in names:
            p = BRAND_DIR / f"{n}{ext}"
            if p.exists():
                return p
    return None


def logo_data_uri(path, max_height: int | None = None) -> str:
    """Embed an image as a data URI (shrunk to max_height pixels when Pillow is available)."""
    if not path or not Path(path).exists():
        return ""
    p = Path(path)
    raw, mime = p.read_bytes(), _MIME.get(p.suffix.lower(), "application/octet-stream")
    if max_height and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
        try:
            import io
            from PIL import Image as _PILImage

            im = _PILImage.open(io.BytesIO(raw))
            if im.height > max_height:
                im = im.resize((max(1, round(im.width * max_height / im.height)), max_height), _PILImage.LANCZOS)
                buf = io.BytesIO()
                if p.suffix.lower() == ".png":
                    im.save(buf, "PNG", optimize=True)
                else:
                    im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True)
                raw = buf.getvalue()
        except Exception:
            pass
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def _pdf_logo() -> list:
    """Logo at the top of the PDF (png/jpg only; reportlab cannot draw svg)."""
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image as _RLImage, Spacer as _Spacer

    p = find_brand_asset(("ribbon_navy", "navy_ribbon"), exts=(".png", ".jpg", ".jpeg"))
    if not p:
        return []
    w, h = ImageReader(str(p)).getSize()
    return [_RLImage(str(p), width=3.2 * inch, height=3.2 * inch * h / w, hAlign="LEFT"), _Spacer(1, 8)]


def build_html(rd: ReportData, figs: dict, brand: Brand = Brand(), client_name: str = "", offline: bool = False,
               inflation_id: str | None = None, curve_id: str | None = None, logo_uri: str | None = None,
               shield_uri: str | None = None, footer_note: str = "") -> str:
    k = rd.kpis
    inflation_id = inflation_id or rd.summary.get("inflation_id", "")
    curve_id = curve_id or rd.summary.get("curve_id", "")
    funded_txt = ("Beyond age %s" % rd.chart_age_limit if (k["fully_funded"] or (k["funded_through_age"] or 0) > (rd.chart_age_limit or 999))
                  else f"Age {k['funded_through_age']} ({k['funded_through_year']})")
    surplus_cls = "pos" if k["surplus"] >= 0 else "neg"
    cards = [
        ("Funding ratio", fmt_pct(k["funding_ratio"]), "of lifetime spending funded", ""),
        ("Surplus / (shortfall)", fmt_money(k["surplus"]), "in today's dollars", surplus_cls),
        ("Savings last through", funded_txt, "if both people are alive", ""),
        ("Peak resources", fmt_money(k["peak_assets"]), f"in {k['peak_asset_year']}", ""),
        ("Retirement", f"Age {k['retirement_age']}", f"{k['retirement_year']}", ""),
        ("Social Security", f"Age {k['ssi_start_age']}", f"from {k['ssi_start_year']}" if k["ssi_start_year"] else "", ""),
    ]
    card_html = "".join(f'<div class="card {c}"><div class="lbl">{_e(a)}</div><div class="val">{_e(b)}</div>'
                        f'<div class="sub">{_e(s)}</div></div>' for a, b, s, c in cards)
    chart_html, first = [], True
    for name, fig in figs.items():
        inc = ("inline" if offline else "cdn") if first else False
        chart_html.append(f'<section class="chart" id="{_e(name)}">' + fig.to_html(full_html=False, include_plotlyjs=inc,
                          config={"displaylogo": False, "responsive": True}) + "</section>")
        first = False
    arows = "".join(f"<tr><th>{_e(a)}</th><td>{_e(b)}</td></tr>" for a, b in assumptions_table(rd, inflation_id, curve_id))
    disc = "".join(f"<li>{_e(d)}</li>" for d in DISCLOSURES + ([brand.extra_disclosure] if brand.extra_disclosure else []))
    who = f" for {_e(client_name)}" if client_name else ""
    title_line = f"{client_name.strip()} {brand.report_title}" if client_name.strip() else brand.report_title
    if logo_uri is None:
        logo_uri = logo_data_uri(find_brand_asset(("ribbon_navy", "navy_ribbon")), 116)
    if shield_uri is None:
        shield_uri = logo_data_uri(find_brand_asset(("shield_cream", "cream_shield", "cream_shield_tn")), 92)
    tag = f"<small>{_e(brand.tagline)}</small>" if brand.tagline else ""
    head_left = (f'<img class="logo" src="{logo_uri}" alt="{_e(brand.firm_name)}">' if logo_uri
                 else f'<div class="firm">{_e(brand.firm_name)}{tag}</div>')
    head_meta = ((f'<div class="prep">Prepared for</div><div class="who">{_e(client_name)}</div>' if client_name else "")
                 + f'<div class="vd">Valuation date {rd.as_of.isoformat()}</div>')
    firm_line = _e(brand.firm_name) + ((" \u00b7 " + _e(brand.tagline)) if brand.tagline else "")
    small = " \u00b7 ".join(x for x in (f"Generated {_e(date.today().isoformat())}", _e(footer_note)) if x)
    foot_html = ('<footer class="bf">' + (f'<img src="{shield_uri}" alt="">' if shield_uri else "")
                 + f'<div>{_e(SHORT_DISCLAIMER)}<br><b>{firm_line}</b><div class="sm">{small}</div></div></footer>')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(brand.report_title)}{who} - {_e(brand.firm_name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="{_FONT_LINK}" rel="stylesheet">
<style>
body{{font-family:{brand.font};color:#1f2937;margin:0;background:#fff}}
.bh{{background:{brand.primary};color:#fff;padding:12px 40px;display:flex;align-items:center;justify-content:space-between;gap:24px}}
.bh .logo{{height:58px;display:block}} .bh .firm{{font-family:'Playfair Display',Georgia,serif;font-size:22px}}
.bh .firm small{{display:block;font-size:12px;opacity:.85}}
.bh .meta{{text-align:right}} .bh .prep{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{brand.accent}}}
.bh .who{{font-family:'Playfair Display',Georgia,serif;font-size:24px;line-height:1.2}} .bh .vd{{font-size:12px;opacity:.85}}
.brule{{height:3px;background:{brand.accent}}}
h1.rt{{font-family:'Playfair Display',Georgia,serif;color:{brand.primary};font-size:26px;margin:4px 0 14px}}
h2{{font-family:'Playfair Display',Georgia,serif}}
footer.bf{{display:flex;align-items:center;gap:16px;border-top:2px solid {brand.accent};margin-top:30px;padding:14px 0}}
footer.bf img{{height:46px;display:block}} footer.bf b{{color:{brand.primary}}} footer.bf .sm{{font-size:11px;opacity:.9}}
.bh,.brule,.card,footer.bf{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
main{{max-width:1100px;margin:0 auto;padding:24px 20px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:8px 0 28px}}
.card{{background:{brand.light};border-radius:10px;padding:16px;border-top:4px solid {brand.accent}}}
.card.pos{{border-top-color:{brand.positive}}} .card.neg{{border-top-color:{brand.negative}}}
.lbl{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:{brand.neutral}}}
.val{{font-size:26px;font-weight:700;color:{brand.primary};margin:4px 0}} .sub{{font-size:12px;color:{brand.neutral}}}
section.chart{{margin:0 0 26px;border:1px solid #E5E7EB;border-radius:10px;padding:6px}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #E5E7EB;font-size:14px}}
th{{width:260px;color:{brand.neutral};font-weight:600}} h2{{color:{brand.primary};margin-top:34px}}
.disc{{font-size:12px;color:#4b5563}} footer{{border-top:1px solid #E5E7EB;margin-top:30px;padding:16px 0;font-size:12px;color:{brand.neutral}}}
@media print{{section.chart{{page-break-inside:avoid}}}}
</style></head><body>
<header class="bh">{head_left}<div class="meta">{head_meta}</div></header><div class="brule"></div>
<main>
<h1 class="rt">{_e(title_line)}</h1>
<div class="cards">{card_html}</div>
{"".join(chart_html)}
<h2>Key assumptions</h2><table>{arows}</table>
<h2>Important information</h2><ul class="disc">{disc}</ul>
{foot_html}
</main></body></html>"""

def write_pngs(figs: dict, out_dir, width: int = 1100, height: int = 520) -> tuple[list[Path], str | None]:
    """Write one PNG per figure. Returns (paths, error). Needs the optional `kaleido` package (and Chrome for kaleido>=1)."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    paths = []
    try:
        for name, fig in figs.items():
            p = out / f"{name}.png"
            fig.write_image(str(p), width=width, height=380 if name == "funding_gauge" else height, scale=2)
            paths.append(p)
    except Exception as e:                                       # kaleido/Chrome missing
        return paths, f"{type(e).__name__}: {str(e)[:300]}"
    return paths, None

def write_pdf(path, rd: ReportData, png_paths: list[Path], brand: Brand = Brand(), client_name: str = "",
              inflation_id: str | None = None, curve_id: str | None = None) -> Path:
    """Simple branded PDF (reportlab): KPI table, charts, assumptions, disclosures."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    k = rd.kpis
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=colors.HexColor(brand.primary), alignment=0)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=colors.HexColor(brand.primary))
    small = ParagraphStyle("small", parent=ss["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#4b5563"))
    story = _pdf_logo() + [Paragraph(html.escape(brand.report_title + (f" - {client_name}" if client_name else "")), h1),
             Paragraph(f"{html.escape(brand.firm_name)} | Valuation date {rd.as_of.isoformat()}", ss["BodyText"]), Spacer(1, 10)]
    funded = "Beyond age %s" % rd.chart_age_limit if k["fully_funded"] else f"Age {k['funded_through_age']} ({k['funded_through_year']})"
    data = [["Funding ratio", fmt_pct(k["funding_ratio"]), "Surplus / (shortfall)", fmt_money(k["surplus"])],
            ["Savings last through", funded, "Peak resources", f"{fmt_money(k['peak_assets'])} ({k['peak_asset_year']})"],
            ["Retirement", f"Age {k['retirement_age']} ({k['retirement_year']})", "Social Security", f"Age {k['ssi_start_age']}"]]
    tbl = Table(data, colWidths=[1.6 * inch, 1.9 * inch, 1.6 * inch, 1.9 * inch])
    tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                             ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(brand.light)), ("BACKGROUND", (2, 0), (2, -1), colors.HexColor(brand.light)),
                             ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"), ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
                             ("FONTSIZE", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [tbl, Spacer(1, 12)]
    for i, p in enumerate(png_paths):
        story.append(Image(str(p), width=7.0 * inch, height=7.0 * inch * (0.35 if "gauge" in p.name else 0.4727)))
        story.append(Spacer(1, 8))
        if i % 2 == 1:
            story.append(PageBreak())
    story += [Paragraph("Key assumptions", h2)]
    arows = [[html.escape(a), html.escape(b)] for a, b in assumptions_table(rd, inflation_id or rd.summary.get("inflation_id", ""), curve_id or rd.summary.get("curve_id", ""))]
    at = Table([[Paragraph(a, small), Paragraph(b, small)] for a, b in arows], colWidths=[2.0 * inch, 5.0 * inch])
    at.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB"))]))
    story += [at, Spacer(1, 10), Paragraph("Important information", h2)]
    story += [Paragraph("&bull; " + html.escape(d), small) for d in DISCLOSURES + ([brand.extra_disclosure] if brand.extra_disclosure else [])]

    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont("Helvetica", 7); canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(0.6 * inch, 0.4 * inch, SHORT_DISCLAIMER); canvas.drawRightString(7.9 * inch, 0.4 * inch, f"Page {doc.page}")
        canvas.restoreState()
    out = Path(path); out.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(out), pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch, topMargin=0.6 * inch,
                      bottomMargin=0.7 * inch, title=brand.report_title, author=brand.firm_name).build(story, onFirstPage=footer, onLaterPages=footer)
    return out

def scenario_table(inputs: ProjectionInputs, tables: ModelTables, ft: ForwardTables, as_of: date) -> pd.DataFrame:
    """Funding ratio under a few adviser-style what-ifs (labels are client-readable)."""
    def ratio(inp=None, curve=None, **kw):
        _, s = run_projection(inp or inputs, tables, ft, as_of, curve=curve, **kw)
        return s["funding_ratio"]
    def changed(**kw):
        return ProjectionInputs(**{**inputs.model_dump(), **kw})
    rows = [("Current plan", ratio())]
    ret = inputs.primary_target_ret_date
    def shift_year(d, n):
        try: return d.replace(year=d.year + n)
        except ValueError: return d.replace(year=d.year + n, day=28)
    rows.append(("Retire 2 years later", ratio(changed(primary_target_ret_date=shift_year(ret, 2)))))
    if shift_year(ret, -1) > date(inputs.first_proj_year, 1, 1):
        rows.append(("Retire 1 year earlier", ratio(changed(primary_target_ret_date=shift_year(ret, -1)))))
    rows.append(("Spend 10% less", ratio(changed(net_expenses=inputs.net_expenses * 0.9))))
    rows.append(("Spend 10% more", ratio(changed(net_expenses=inputs.net_expenses * 1.1))))
    rows.append(("Inflation 1 point higher", ratio(changed(inflation_load=inputs.inflation_load + 0.01))))
    rows.append(("Interest rates 1 point higher", ratio(curve=tables.legacy_curve().with_spread(0.01))))
    rows.append(("Interest rates 1 point lower", ratio(curve=tables.legacy_curve().with_spread(-0.01))))
    return pd.DataFrame(rows, columns=["label", "funding_ratio"])
