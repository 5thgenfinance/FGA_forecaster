# Branding install
1. Unzip over FGA_forecaster (adds assets/brand, brand/fga_brand.json, model/branding.py, app/branding_ui.py, .streamlit/config.toml).
2. In app/ui.py, after st.set_page_config(...):  
   from app.branding_ui import apply_branding; apply_branding()
3. Charts: call model.branding.apply_to_figure(fig) before display/export.
4. Report: put <style>{report_css()}</style> in the HTML head and use logo_data_uri("ribbon", dark_surface=True) in a navy header band.
5. Restart: python -m streamlit run app/ui.py
Logos are JPEG (no transparency): use the cream versions on off-white, navy/white versions on navy.
