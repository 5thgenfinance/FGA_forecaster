from datetime import date
import pytest
from app import header_html as H

def test_title_escapes_and_prompts_when_empty():
    t = H.title_html("<script>alert(1)</script> & Co", date(2026, 11, 5))
    assert "<script>" not in t and "&lt;script&gt;" in t and "Prepared for" in t and "November 5, 2026" in t
    f = H.title_html("  ", date(2026, 11, 5))
    assert "Add a client name" in f and "Prepared for" not in f and "fga-empty" in f

def test_assets_resolve_and_prefer_vector(tmp_path, monkeypatch):
    for n in ("shield_navy", "shield_cream", "ribbon_navy"):
        assert H.asset_path(n).exists()
    assert H.favicon_path().exists()
    monkeypatch.setattr(H, "ASSETS", tmp_path)
    (tmp_path / "x.jpg").write_bytes(b"j"); assert H.asset_path("x").suffix == ".jpg"
    (tmp_path / "x.png").write_bytes(b"p"); assert H.asset_path("x").suffix == ".png"
    (tmp_path / "x.svg").write_text("<svg/>"); assert H.asset_path("x").suffix == ".svg"
    assert H.data_uri("x").startswith("data:image/svg+xml;base64,")
    with pytest.raises(FileNotFoundError): H.asset_path("nope")

def test_blocks_and_css():
    assert H.PRODUCT == "Fifth Generation Retirement Illustrator" and H.PRODUCT in H.brand_block_html()
    f = H.footer_html(); assert "Hypothetical illustration" in f and "Registered Investment Adviser" in f
    css = H.header_css()
    assert "#1a2744" in css and "#c49a4a" in css and "$" not in css and css.count("{") == css.count("}")
    assert "position:sticky" in css
