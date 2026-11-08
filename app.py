"""SARC-Tool: Streamlit entry point."""
import streamlit as st

from sarc import meta
from sarc.i18n import t
from sarc.ui import components as ui
from sarc.ui import tabs

st.set_page_config(page_title=meta.APP_NAME, page_icon=str(ui.LOGO), layout="wide")
ui.inject_style()

lang = "pt" if st.sidebar.selectbox("Idioma / Language", ["Português", "English"], key="lang") == "Português" else "en"
params = tabs.sidebar_params(lang)
api_key, model, provider = tabs.sidebar_llm(lang)
ui.sidebar_footer(lang)

ui.header(lang)
names = ["tab_data", "tab_sarc", "tab_comp", "tab_diag", "tab_plots", "tab_export"]
if api_key:
    names.append("tab_ai")
names.append("tab_about")
tb = dict(zip(names, st.tabs([t(n, lang) for n in names])))

with tb["tab_data"]:
    setup = tabs.data_tab(lang, params)
with tb["tab_sarc"]:
    tabs.sarc_tab(lang, setup)
with tb["tab_comp"]:
    tabs.comp_tab(lang, setup)
with tb["tab_diag"]:
    tabs.diag_tab(lang, setup)
with tb["tab_plots"]:
    tabs.plots_tab(lang, setup)
with tb["tab_export"]:
    tabs.export_tab(lang, setup)
if api_key:
    with tb["tab_ai"]:
        tabs.ai_tab(lang, setup, api_key, model, provider)
with tb["tab_about"]:
    ui.about(lang)
