"""Report branding: logo header, client name, branded footer. Runs the real model on the default inputs."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from model.dashboard import Brand, build_figures, build_report_data
from model.engine import ModelTables
from model.inputs import ProjectionInputs
from model.loop import ForwardTables
from model.report import build_html, find_brand_asset

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def report_data():
    t, ft = ModelTables.from_csv_dir(str(DATA)), ForwardTables.from_csv_dir(str(DATA))
    rd = build_report_data(ProjectionInputs(), t, ft, date(2026, 11, 6))
    return rd, build_figures(rd, Brand(), None)


def test_branded_header_and_footer(report_data):
    rd, figs = report_data
    html = build_html(rd, figs, Brand(), client_name="Ann & <b>Bo</b>", footer_note="Version 9.9.9")
    assert 'class="bh"' in html and 'class="bf"' in html
    assert "Ann &amp; &lt;b&gt;Bo&lt;/b&gt;" in html and "<b>Bo</b>" not in html      # escaped
    assert "Version 9.9.9" in html and "Generated " in html
    assert html.count("<header") == 1 and html.count("<footer") == 1
    if find_brand_asset(("ribbon_navy", "navy_ribbon")):
        assert "data:image" in html


def test_no_logo_falls_back_to_text(report_data):
    rd, figs = report_data
    html = build_html(rd, figs, Brand(), logo_uri="", shield_uri="")
    assert 'class="firm"' in html and "data:image" not in html


def test_title_includes_client_name(report_data):
    rd, figs = report_data
    assert "for Ann" in build_html(rd, figs, Brand(), client_name="Ann")
