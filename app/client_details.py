"""Client details page: client name, input containers (Personal, Income, Expenses, Accounts, Mortgage), JSON save/load."""
from __future__ import annotations
from datetime import date
import streamlit as st
from app import client_io
from app.ui_helpers import HELP, INPUT_GROUPS, LABELS, PCT_FIELDS, choices, field_kind, form_to_inputs

CLIENT_GROUPS: dict[str, list[str]] = {
    "Personal": [f for f in INPUT_GROUPS["Personal"] if f != "mort_table"],
    "Income": INPUT_GROUPS["Income"],
    "Expenses": INPUT_GROUPS["Expenses"],
    "Accounts": INPUT_GROUPS["Accounts"],
    "Mortgage": INPUT_GROUPS["Mortgage"],
}
CLIENT_FIELDS = [f for fs in CLIENT_GROUPS.values() for f in fs]
SIDEBAR_GROUPS = {("Mortality" if g == "Personal" else g): ([f for f in fs if f not in set(CLIENT_FIELDS)])
                  for g, fs in INPUT_GROUPS.items() if g not in CLIENT_GROUPS or g == "Personal"}
SIDEBAR_GROUPS = {g: fs for g, fs in SIDEBAR_GROUPS.items() if fs}
SPOUSE_ONLY = ("s_dob", "t_s_ret_date")


def widget(name: str, default, key: str):
    label, kind, help_ = LABELS.get(name, name), field_kind(name), HELP.get(name)
    if kind == "bool":
        return st.checkbox(label, value=bool(default), key=key, help=help_)
    if kind == "date":
        return st.date_input(label, value=default or date(1970, 1, 1), min_value=date(1900, 1, 1),
                             max_value=date(2100, 12, 31), key=key, help=help_)
    if kind == "int":
        return st.number_input(label, value=int(default), step=1, key=key, help=help_)
    if kind == "float":
        step = 0.1 if name in PCT_FIELDS else 1000.0
        return st.number_input(label, value=float(default), step=step, key=key, help=help_)
    if kind == "choice":
        opts = choices(name)
        return st.selectbox(label, opts, index=opts.index(default) if default in opts else 0, key=key, help=help_)
    return st.text_input(label, value=str(default), key=key, help=help_)


def apply_pending_import(store: dict) -> None:
    """Run at the very top of main(), before any widget is created."""
    pending = st.session_state.pop("pending_import", None)
    if not pending:
        return
    from app.ui_helpers import to_form_values
    fv = to_form_values(pending["inputs"])
    store.update({f: fv[f] for f in CLIENT_FIELDS})
    for f in CLIENT_FIELDS:                      # client-page widgets are keyed cd_<field>
        st.session_state[f"cd_{f}"] = fv[f]
    for fs in SIDEBAR_GROUPS.values():          # sidebar widgets are keyed by field name
        for f in fs:
            st.session_state[f] = fv[f]
    st.session_state["client_name"] = pending["client_name"]
    st.session_state["cd_client_name"] = pending["client_name"]
    st.session_state["import_notice"] = f"Loaded {pending['filename']}."


def client_page(store: dict, sidebar_values: dict, valuation_date: date) -> None:
    st.header("Client details")
    # --- instructions placeholder: add your text here ---
    if notice := st.session_state.pop("import_notice", None):
        st.success(notice)
    name = st.text_input("Client name", value=st.session_state.get("client_name", ""), key="cd_client_name")
    st.session_state["client_name"] = client_io.clean_name(name)
    io_box = st.container(border=True)

    slots: dict[str, object] = {}
    for group, fields in CLIENT_GROUPS.items():
        with st.container(border=True):
            st.subheader(group)
            cols = st.columns(3)
            i = 0
            for f in fields:
                if f in SPOUSE_ONLY and not store.get("include_spouse", True):
                    continue
                with cols[i % 3]:
                    store[f] = widget(f, store[f], f"cd_{f}")
                    slots[f] = st.empty()
                i += 1

    inputs, errors = form_to_inputs({**sidebar_values, **store})
    shown = set()
    for f, msg in errors.items():
        if f in slots:
            slots[f].error(msg); shown.add(f)
    other = {f: m for f, m in errors.items() if f not in shown}

    with io_box:
        st.subheader("Save or load client file")
        c1, c2 = st.columns(2)
        with c1:
            if inputs is not None:
                c1.download_button("Export client file (JSON)",
                                   client_io.build_export(inputs, st.session_state["client_name"], valuation_date),
                                   client_io.file_name(st.session_state["client_name"]), "application/json")
            else:
                c1.warning("Fix the highlighted inputs before exporting.")
        with c2:
            n = st.session_state.setdefault("upload_n", 0)
            up = c2.file_uploader("Import client file (JSON)", type=["json"], key=f"cd_upload_{n}")
            if up is not None:
                res = client_io.parse_import(up.getvalue())
                if res.errors:
                    for e in res.errors:
                        c2.error(e)
                elif c2.button("Apply imported file", type="primary"):
                    st.session_state["pending_import"] = {"inputs": res.inputs, "client_name": res.client_name,
                                                          "filename": up.name}
                    st.session_state["upload_n"] = n + 1
                    st.rerun()
        for f, msg in other.items():
            st.error(f"{LABELS.get(f, f)}: {msg}")
