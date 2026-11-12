"""Top ribbon (settings cog + client head) and the two pages it opens."""
from __future__ import annotations
import streamlit as st
from model import branding as B
from model import table_store as TS

VIEWS = ("forecast", "settings", "client", "help")
_CSS = """<style>
.block-container { padding-top: 1rem !important; }
header[data-testid="stHeader"] { background: transparent; }
</style>"""


def current_view() -> str:
    return st.session_state.get("view", "forecast")


def _go(view: str) -> None:
    st.session_state["view"] = view


def render_topbar() -> None:
    """Call first on every run, after apply_branding(). Logo left, icons right, tight together."""
    st.markdown(_CSS, unsafe_allow_html=True)
    left, c1, c2, c3 = st.columns([18, 1, 1, 1], gap="small", vertical_alignment="center")
    c3.button("", icon=":material/help:", key="btn_help", help="User guide",
              type="primary" if current_view() == "help" else "secondary",
              on_click=_go, args=("help" if current_view() != "help" else "forecast",))
    with left:
        st.image(str(B.logo_path("ribbon", dark_surface=False)), width=220)
    v = current_view()
    c1.button("", icon=":material/settings:", key="btn_settings", help="Model tables",
              type="primary" if v == "settings" else "secondary",
              on_click=_go, args=("settings" if v != "settings" else "forecast",))
    c2.button("", icon=":material/person:", key="btn_client", help="Client details",
              type="primary" if v == "client" else "secondary",
              on_click=_go, args=("client" if v != "client" else "forecast",))
    st.markdown("<hr style='margin:0 0 8px'>", unsafe_allow_html=True)


def settings_page() -> None:
    st.header("Model tables")
    # --- instructions placeholder: add your text here ---
    if TS.is_customised():
        st.info("Using your edited tables (data_user/). Originals in data/ are untouched.")
    label = st.selectbox("Table", list(TS.TABLES))
    stem = TS.TABLES[label]
    df = TS.load(stem)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True,
                            key=f"ed_{stem}_{'_'.join(map(str, df.columns))}")
    errs = TS.validate(stem, edited)
    for e in errs:
        st.error(e)
    a, b, c = st.columns(3)
    if a.button("Save changes", type="primary", disabled=bool(errs)):
        TS.save(stem, edited)
        st.cache_data.clear()
        st.success(f"Saved {label}. Go back to the forecast to see the effect.")
    if b.button(f"Reset {label}"):
        TS.reset(stem); st.cache_data.clear(); st.rerun()
    if c.button("Reset all tables"):
        TS.reset(); st.cache_data.clear(); st.rerun()
    with st.expander("Add or remove columns"):
        st.caption("Save any row edits first: adding or removing a column reloads the table from the last save. "
                   "The model only reads columns it already knows, so added columns are stored but unused "
                   "until the model is extended to use them.")
        n1, n2, n3 = st.columns([3, 2, 2])
        cname = n1.text_input("New column name", key=f"cn_{stem}")
        ckind = n2.selectbox("Type", ["number", "text"], key=f"ck_{stem}")
        cdef = n3.text_input("Default value (optional)", key=f"cd_{stem}")
        if st.button("Add column", key=f"ac_{stem}"):
            try:
                TS.add_column(stem, cname, ckind, cdef); st.cache_data.clear(); st.rerun()
            except ValueError as e:
                st.error(str(e))
        extras = TS.extra_columns(stem, df)
        if extras:
            drop = st.selectbox("Remove an added column", extras, key=f"dc_{stem}")
            if st.button("Remove column", key=f"rc_{stem}"):
                TS.drop_column(stem, drop); st.cache_data.clear(); st.rerun()
    st.download_button("Download this table (CSV)", edited.to_csv(index=False), f"{stem}.csv")


CLIENT_FIELDS = [("client_name", "Client name(s)"), ("adviser", "Adviser"),
                 ("email", "Email"), ("phone", "Phone"), ("notes", "Notes")]


def client_page() -> None:
    st.header("Client details")
    # --- instructions placeholder: add your text here ---
    d = st.session_state.setdefault("client", {})
    with st.form("client_form"):
        for k, lab in CLIENT_FIELDS:
            d[k] = (st.text_area if k == "notes" else st.text_input)(lab, value=d.get(k, ""))
        if st.form_submit_button("Save client details", type="primary"):
            st.session_state["client"] = d
            st.success("Saved for this session.")
    st.caption("Model inputs (dates of birth, balances, etc.) are still entered in the sidebar on the forecast page.")


def help_page() -> None:
    # Full-page user guide (docs/USER_GUIDE.md).
    from app.help_page import render_help_page

    st.button("Back to forecast", icon=":material/arrow_back:", key="help_back", on_click=_go, args=("forecast",))
    render_help_page()
