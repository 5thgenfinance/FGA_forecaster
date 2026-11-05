"""Streamlit rendering: full-width navy header, page title, footer."""
from __future__ import annotations
import streamlit as st
from app import header_html as H


def _go(view: str) -> None:
    st.session_state["view"] = view


def render_header() -> None:
    """Call once per run, after apply_branding() and before routing to a view."""
    st.markdown(f"<style>{H.header_css()}</style>", unsafe_allow_html=True)
    v = st.session_state.get("view", "forecast")
    with st.container(key="fga_header"):
        left, c1, c2 = st.columns([30, 1, 1], gap="small", vertical_alignment="center")
        left.markdown(H.brand_block_html(), unsafe_allow_html=True)
        c1.button("", icon=":material/settings:", key="btn_settings", help="Model tables",
                  type="primary" if v == "settings" else "secondary",
                  on_click=_go, args=("forecast" if v == "settings" else "settings",))
        c2.button("", icon=":material/person:", key="btn_client", help="Client details",
                  type="primary" if v == "client" else "secondary",
                  on_click=_go, args=("forecast" if v == "client" else "client",))


def render_title(client_name: str | None, as_of) -> None:
    st.markdown(H.title_html(client_name, as_of), unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(H.footer_html(), unsafe_allow_html=True)
