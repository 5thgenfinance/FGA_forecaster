"""Call apply_branding() once, right after st.set_page_config in app/ui.py."""
import streamlit as st
from model import branding as B


def render_header(title: str = "Retirement Forecast", width: int = 300) -> None:
    st.image(str(B.logo_path("ribbon", dark_surface=False)), width=width)
    st.title(title)

def apply_branding(sidebar_logo: bool = True) -> None:
    st.markdown(f"<style>{B.web_css()}</style>", unsafe_allow_html=True)
    if sidebar_logo:
        st.sidebar.image(str(B.logo_path("ribbon", dark_surface=False)), use_container_width=True)
    #st.caption(f"{B.BRAND['firm_name']} \u00b7 {B.BRAND['tagline']}")
