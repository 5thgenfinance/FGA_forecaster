"""Navy input pane with white text and light-blue containers. Call apply_sidebar_theme() right after apply_branding()."""
import streamlit as st

NAVY, BRONZE = "#1a2744", "#c49a4a"
LIGHT_BLUE = "#dfe7f3"      # container fill; change this one value to tune the shade
FIELD_BG = "#ffffff"
CHARCOAL = "#2c2c2c"

# NOTE: this is an f-string, so every literal CSS brace is doubled ({{ }}).
CSS = f"""
<style>
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{ background:{NAVY} !important; }}
[data-testid="stSidebar"] {{ border-right:1px solid {BRONZE}; }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:#ffffff; }}
[data-testid="stSidebar"] svg {{ fill:#ffffff; }}

[data-testid="stSidebar"] [data-testid="stExpander"] details {{
    background:{LIGHT_BLUE}; border:1px solid {BRONZE}; border-radius:8px; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] label,
[data-testid="stSidebar"] [data-testid="stExpander"] p,
[data-testid="stSidebar"] [data-testid="stExpander"] span,
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stCaptionContainer"] {{ color:{NAVY}; }}
[data-testid="stSidebar"] [data-testid="stExpander"] svg {{ fill:{NAVY}; }}

[data-testid="stSidebar"] [data-baseweb="input"], [data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"], [data-testid="stSidebar"] [data-testid="stDateInput"] > div:not([data-testid="stWidgetLabel"]) {{
    background:{FIELD_BG} !important; }}
[data-testid="stSidebar"] [data-baseweb="input"] *, [data-testid="stSidebar"] [data-baseweb="base-input"] *,
[data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] input {{
    color:{CHARCOAL} !important; -webkit-text-fill-color:{CHARCOAL} !important; }}

[data-testid="stSidebar"] [data-testid="stDateInput"] *,
[data-testid="stSidebar"] [data-testid="stDateInput"] input,
[data-testid="stSidebar"] [data-testid="stDateInput"] [role="spinbutton"],
[data-testid="stSidebar"] [data-testid="stDateInput"] [role="presentation"] {{
    color:{CHARCOAL} !important; -webkit-text-fill-color:{CHARCOAL} !important; opacity:1 !important; }}
[data-testid="stSidebar"] [data-testid="stDateInput"] svg {{ fill:{CHARCOAL} !important; }}
[data-testid="stSidebar"] [data-testid="stDateInput"] [data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] [data-testid="stDateInput"] label * {{
    color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }}

[data-testid="stSidebar"] [data-baseweb="input"] svg, [data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill:{CHARCOAL} !important; }}
[data-testid="stSidebar"] button[kind="secondary"] {{ background:{LIGHT_BLUE}; color:{NAVY}; border:1px solid {BRONZE}; }}

/* banner at the top of the pane */
[data-testid="stSidebarHeader"] {{ min-height:2.25rem; height:2.25rem; padding-bottom:0; }}
[data-testid="stSidebarUserContent"] {{ padding-top:0 !important; }}
[data-testid="stSidebar"] [data-testid="stImage"] {{ margin-bottom:8px; }}
</style>
"""


def apply_sidebar_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
