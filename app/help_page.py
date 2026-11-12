"""In-app help: the full-page guide (Help button in the header) and a short sidebar panel.
Source text: docs/USER_GUIDE.md. Streamlit is imported inside the functions so the helpers can be unit-tested."""
from __future__ import annotations
import re
from pathlib import Path

GUIDE_MD = Path(__file__).resolve().parents[1] / "docs" / "USER_GUIDE.md"
GUIDE_PDF = GUIDE_MD.with_suffix(".pdf")


def guide_text() -> str:
    return GUIDE_MD.read_text(encoding="utf8") if GUIDE_MD.exists() else "The user guide file (docs/USER_GUIDE.md) was not found."


def split_sections(md: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (intro, [(title, body_markdown), ...]) splitting on level-2 headings."""
    parts = re.split(r"(?m)^## ", md)
    intro, rest = parts[0], parts[1:]
    out = []
    for p in rest:
        title, _, body = p.partition("\n")
        out.append((title.strip(), "## " + title.strip() + "\n" + body))
    return intro, out


def filter_sections(sections: list[tuple[str, str]], query: str) -> list[tuple[str, str]]:
    q = query.strip().lower()
    return [s for s in sections if q in s[1].lower()] if q else sections


def render_help_page() -> None:
    """Full-page guide with a jump menu and a search box."""
    import streamlit as st

    intro, sections = split_sections(guide_text())
    st.markdown(intro)
    c1, c2, c3 = st.columns([2, 2, 3], vertical_alignment="bottom")
    query = c1.text_input("Search the guide", key="help_search", placeholder="e.g. Social Security")
    found = filter_sections(sections, query)
    titles = [t for t, _ in found]
    choice = c2.selectbox("Go to section", ["All sections"] + titles, key="help_section")
    with c3:
        if GUIDE_PDF.exists():
            st.download_button("Download as PDF", GUIDE_PDF.read_bytes(), "User_Guide.pdf", "application/pdf", key="help_pdf")
    if query and not found:
        st.info("No section mentions that. Try a shorter word.")
    for title, body in found:
        if choice in ("All sections", title):
            st.markdown(body)


def render_help_sidebar() -> None:
    """Optional short panel for the sidebar; the header Help button is the main entry point."""
    import streamlit as st

    with st.sidebar.expander("Help", expanded=False):
        st.caption("Hover over a ? next to any field for a short explanation. The full guide is under the ? button in the header.")
        if GUIDE_PDF.exists():
            st.download_button("Download user guide (PDF)", GUIDE_PDF.read_bytes(), "User_Guide.pdf", "application/pdf", key="help_dl_pdf")
