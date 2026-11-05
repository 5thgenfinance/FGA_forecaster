import re
from model import branding as B

def test_palette_exact():
    assert (B.NAVY, B.BRONZE, B.OFFWHITE, B.CHARCOAL) == ("#1a2744", "#c49a4a", "#f7f4ef", "#2c2c2c")

def test_logos_exist():
    for k in ("shield", "ribbon"):
        for d in (False, True):
            assert B.logo_path(k, d).exists()

def test_css_uses_brand_fonts():
    css = B.report_css()
    assert "Playfair Display" in css and "Source Sans 3" in css and B.BRONZE in css

def test_data_uri():
    assert B.logo_data_uri().startswith("data:image/jpeg;base64,")

def test_chart_template():
    assert B.plotly_layout()["colorway"][0] == B.NAVY
