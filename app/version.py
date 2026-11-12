"""Single source of truth for the application version shown in the footer.

Change APP_VERSION here (and nowhere else) when you release. Keep major.minor in step with the
specification version (SPEC.md title), e.g. spec 1.2 -> app 1.2.x.
"""
from __future__ import annotations

import os
import subprocess
from datetime import date
from functools import lru_cache
from pathlib import Path

APP_VERSION = "1.2.0"
RELEASE_DATE = "2026-11-12"          # update with each release
PRODUCT = "Fifth Generation Retirement Illustrator"


@lru_cache(maxsize=1)
def build_id() -> str:
    """Short git commit if available, else the FGA_BUILD environment variable, else empty."""
    env = os.environ.get("FGA_BUILD", "").strip()
    if env:
        return env[:12]
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).resolve().parents[1],
                             capture_output=True, text=True, timeout=2)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def version_line(include_build: bool = True) -> str:
    """e.g. 'Version 1.2.0 · released 2026-11-12 · build a1b2c3d'."""
    parts = [f"Version {APP_VERSION}", f"released {RELEASE_DATE}"]
    b = build_id() if include_build else ""
    if b:
        parts.append(f"build {b}")
    return " \u00b7 ".join(parts)


def render_version_footer() -> None:
    """Stand-alone footer line. Use only if the branded footer cannot be edited."""
    import streamlit as st

    st.markdown(
        f"<div style='text-align:center;font-size:0.75rem;color:#8a93a8;margin-top:0.5rem'>{version_line()}</div>",
        unsafe_allow_html=True,
    )
