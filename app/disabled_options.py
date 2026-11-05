"""Greys out and blocks dropdown options whose text contains a marker, e.g. "IAM2012 (coming soon)".
Streamlit cannot disable a single selectbox option, so a tiny script in a zero-height component styles the open list."""
from __future__ import annotations
import json
import streamlit.components.v1 as components
from app.mortality_options import MARKER

_JS = """
<script>
(function () {
  const win = window.parent, doc = win.document, MARK = %s;
  if (win.__fgaGrey) return;
  win.__fgaGrey = true;
  const st = doc.createElement('style');
  st.textContent = 'li[role="option"].fga-disabled{opacity:.45 !important;color:#8a93a8 !important;' +
                   'cursor:not-allowed !important;pointer-events:none !important;font-style:italic;}';
  doc.head.appendChild(st);
  const mark = () => doc.querySelectorAll('li[role="option"]').forEach(li => {
    if (li.textContent.indexOf(MARK) !== -1) { li.classList.add('fga-disabled'); li.setAttribute('aria-disabled', 'true'); }
  });
  new MutationObserver(mark).observe(doc.body, {childList: true, subtree: true});
  mark();
})();
</script>
"""


def grey_out_options(marker: str = MARKER) -> None:
    components.html(_JS % json.dumps(marker), height=0)
