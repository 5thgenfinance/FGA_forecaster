# Ribbon, settings and client pages (v2)
In app/ui.py (after st.set_page_config and apply_branding(sidebar_logo=False)):

    from app.shell import render_topbar, current_view, settings_page, client_page
    from model import table_store as TS
    render_topbar()                      # draws the logo itself; remove render_header()
    view = current_view()
    if view == "settings": settings_page(); st.stop()
    if view == "client":   client_page();   st.stop()
    # ...existing forecast page continues below...

Load tables from the edited folder:
    ModelTables.from_csv_dir(TS.effective_dir()); ForwardTables.from_csv_dir(TS.effective_dir())
Key any @st.cache_data loader on str(TS.effective_dir()). Add data_user/ to .gitignore.
