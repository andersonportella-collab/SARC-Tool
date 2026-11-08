"""Reusable Streamlit components: style, header, sidebar footer, citation and authors."""
from pathlib import Path

import pandas as pd
import streamlit as st

from .. import meta
from ..i18n import t
from ..params import DEFAULT

ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "assets" / "logo.png"
MANUALS = {"pt": ROOT / "docs" / "MANUAL_PT.md", "en": ROOT / "docs" / "MANUAL_EN.md"}

COLORS = dict(primary="#003366", secondary="#0066CC", accent="#FF6600", success="#28A745",
              neutral="#6C757D", background="#F8F9FA", text="#212529")


def inject_style():
    c = COLORS
    st.markdown(f"""
<style>
  .stButton > button[kind="primary"] {{ background-color:{c['primary']}; border-color:{c['primary']}; }}
  .stButton > button[kind="primary"]:hover {{ background-color:{c['secondary']}; border-color:{c['secondary']}; }}
  div[data-testid="stMetric"] {{ background:{c['background']}; border-left:4px solid {c['primary']};
      padding:8px 12px; border-radius:4px; }}
  .sarc-sub {{ color:{c['neutral']}; margin-top:-0.6rem; }}
  .sarc-inst {{ color:{c['primary']}; font-weight:600; font-size:0.9rem; }}
  .sarc-foot {{ font-size:0.8rem; color:{c['neutral']}; }}
</style>""", unsafe_allow_html=True)


def header(lang):
    c1, c2 = st.columns([1, 4], vertical_alignment="center")
    with c1:
        if LOGO.exists():
            st.image(str(LOGO), width=170)
    with c2:
        st.title(meta.APP_NAME)
        st.markdown(f"<div class='sarc-sub'>{t('subtitle', lang)}</div>", unsafe_allow_html=True)
        inst = " · ".join(meta.INSTITUTIONS[k][lang] for k in ("UFF", "EGN"))
        st.markdown(f"<div class='sarc-inst'>{inst}</div>", unsafe_allow_html=True)


def sidebar_footer(lang):
    st.sidebar.divider()
    st.sidebar.markdown(f"<div class='sarc-foot'>{t('version', lang)} {meta.VERSION} · INPI {meta.INPI}</div>",
                        unsafe_allow_html=True)
    st.sidebar.markdown(f"**{t('support', lang)}**  \n[{meta.SUPPORT_EMAIL}](mailto:{meta.SUPPORT_EMAIL})")


def defaults_table(lang):
    d = DEFAULT
    rows = [("K", "50, 100, 200"), (t("eps_tie", lang), d.eps_tie), (t("tol_active", lang), d.tol_active),
            (t("eps_center", lang), d.eps_center), (t("eps_ambig", lang), d.eps_ambig), ("VIKOR v", d.vikor_v),
            ("τ-b", "postos médios" if lang == "pt" else "average ranks"),
            (t("theta_shift", lang), f"> {d.theta_shift_alert}"), (t("area_diff", lang), f"> {d.area_diff_alert}")]
    return pd.DataFrame(rows, columns=["", "valor" if lang == "pt" else "value"]).astype(str)


def about(lang):
    st.subheader(t("about_method", lang))
    st.write(t("about_text", lang))
    st.subheader(t("limits", lang))
    st.markdown("\n".join(f"- {x}" for x in t("limits_list", lang)))
    st.subheader(t("defaults", lang))
    st.dataframe(defaults_table(lang), hide_index=True)

    st.subheader(t("cite", lang))
    abnt, apa, bib = meta.software_citation(lang)
    st.markdown(f"**{t('cite_soft', lang)}**")
    a, b, c = st.tabs(["ABNT", "APA", "BibTeX"])
    with a:
        st.markdown(abnt)
    with b:
        st.markdown(apa)
    with c:
        st.code(bib, language="bibtex")
    st.markdown(f"**{t('cite_art', lang)}**")
    art = meta.article_citation()
    if art:
        x, y = st.tabs(["ABNT", "APA"])
        with x:
            st.markdown(art[0])
        with y:
            st.markdown(art[1])
    else:
        st.info(t("cite_art_pending", lang))

    st.subheader(t("authors", lang))
    cols = st.columns(len(meta.AUTHORS))
    for col, au in zip(cols, meta.AUTHORS):
        with col:
            st.markdown(f"**{au['name']}**")
            st.caption(meta.INSTITUTIONS[au["inst"]][lang])
            st.markdown(f"[ORCID {au['orcid']}](https://orcid.org/{au['orcid']})")
    man = MANUALS[lang]
    if man.exists():
        st.download_button(t("manual", lang), man.read_bytes(), man.name, "text/markdown")
    st.caption(t("license", lang) + f" [{meta.REPO_URL}]({meta.REPO_URL})")
