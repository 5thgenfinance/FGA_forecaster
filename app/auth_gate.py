"""Shared-password gate for the Streamlit app.

Setup: put the password in .streamlit/secrets.toml (local) or the app's Secrets box (Streamlit Cloud):

    app_password = "a-long-passphrase"
    # optional: accept several during a rotation
    # app_passwords = ["new-passphrase", "old-passphrase"]

If no password is configured the gate is OFF and the app opens normally (so local development works).
Set  require_password = true  in the secrets to make a missing password an error instead (recommended when deployed).
"""
from __future__ import annotations

import hmac
import time

MAX_TRIES = 5          # wrong attempts per session before a pause
LOCK_SECONDS = 30


def password_ok(entered: str, accepted: list[str]) -> bool:
    """Constant-time comparison against every accepted password (no early exit)."""
    ok = False
    for p in accepted:
        ok |= hmac.compare_digest(entered.encode("utf8"), p.encode("utf8"))
    return ok


def accepted_passwords(secrets) -> list[str]:
    out: list[str] = []
    try:
        if "app_password" in secrets:
            out.append(str(secrets["app_password"]))
        if "app_passwords" in secrets:
            out += [str(x) for x in secrets["app_passwords"]]
    except Exception:  # no secrets file at all
        return []
    return [p for p in out if p]


def gate() -> None:
    """Call right after st.set_page_config(...) and before anything else is drawn."""
    import streamlit as st

    try:
        secrets = st.secrets
        accepted = accepted_passwords(secrets)
        required = bool(secrets.get("require_password", False))
    except Exception:
        accepted, required = [], False
    if not accepted:
        if required:
            st.error("This app is not configured correctly: no password is set.")
            st.stop()
        return
    if st.session_state.get("auth_ok"):
        with st.sidebar:
            if st.button("Sign out", key="auth_signout"):
                st.session_state.clear()
                st.rerun()
        return

    st.title("Sign in")
    now = time.time()
    locked_until = st.session_state.get("auth_locked_until", 0.0)
    if now < locked_until:
        st.warning(f"Too many attempts. Try again in {int(locked_until - now) + 1} seconds.")
        st.stop()
    with st.form("auth_form"):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Continue")
    if submitted:
        if password_ok(entered, accepted):
            st.session_state["auth_ok"] = True
            st.session_state["auth_fails"] = 0
            st.rerun()
        fails = st.session_state.get("auth_fails", 0) + 1
        st.session_state["auth_fails"] = fails
        if fails >= MAX_TRIES:
            st.session_state["auth_locked_until"] = now + LOCK_SECONDS
            st.session_state["auth_fails"] = 0
        st.error("Incorrect password.")
    st.stop()
