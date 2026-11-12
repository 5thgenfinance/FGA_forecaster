from app.help_page import filter_sections, guide_text, split_sections


def test_sections_split_and_cover_guide():
    intro, secs = split_sections(guide_text())
    titles = " ".join(t for t, _ in secs)
    assert "Quick start" in titles and len(secs) >= 8
    assert "User Guide" in intro


def test_search_filters():
    _, secs = split_sections(guide_text())
    hits = filter_sections(secs, "Social Security")
    assert hits and len(hits) < len(secs)
    assert filter_sections(secs, "") == secs
    assert filter_sections(secs, "zzzz-not-there") == []
