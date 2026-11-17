"""Tab renderers of the SARC-Tool interface."""
import json
import time
from collections import OrderedDict
from dataclasses import replace

import numpy as np
import pandas as pd
import streamlit as st

from .. import data_io as dio
from .. import plots, llm
from ..analysis import analyze, summary
from ..core import prepare
from ..i18n import t, ml
from ..params import DEFAULT, M_MAX, M_WARN, N_MAX


# ---------------------------------------------------------------- sidebar parameters
def sidebar_params(lang):
    sb = st.sidebar
    sb.subheader(t("params", lang))
    sb.caption(t("params_frozen", lang))
    with sb.expander(t("advanced", lang)):
        if st.button(t("reset", lang)):
            for k in ("p_K", "p_tie", "p_act", "p_cen", "p_amb", "p_v"):
                st.session_state.pop(k, None)
        K = st.multiselect(t("K_list", lang), [25, 50, 100, 150, 200, 300], default=list(DEFAULT.K_list), key="p_K")
        tie = st.number_input(t("eps_tie", lang), value=DEFAULT.eps_tie, format="%.1e", step=None, key="p_tie")
        act = st.number_input(t("tol_active", lang), value=DEFAULT.tol_active, format="%.1e", step=None, key="p_act")
        cen = st.number_input(t("eps_center", lang), value=DEFAULT.eps_center, format="%.1e", step=None, key="p_cen")
        amb = st.number_input(t("eps_ambig", lang), value=DEFAULT.eps_ambig, format="%.1e", step=None, key="p_amb")
        v = st.slider(t("vikor_v", lang), 0.0, 1.0, DEFAULT.vikor_v, 0.05, key="p_v")
    K = tuple(sorted(K)) or DEFAULT.K_list
    return replace(DEFAULT, K_list=K, eps_tie=float(tie), tol_active=float(act), eps_center=float(cen),
                   eps_ambig=float(amb), vikor_v=float(v))


def sidebar_llm(lang):
    with st.sidebar.expander(t("llm_exp", lang)):
        prov = st.radio(t("llm_provider", lang), llm.PROVIDERS, format_func=llm.PROVIDER_LABELS.get, key="llm_provider")
        key = st.text_input(t("llm_key_" + prov, lang), type="password", help=t("llm_key_help", lang),
                            key=f"llm_key_{prov}")
        model = st.text_input(t("llm_model", lang), value=llm.DEFAULT_MODELS[prov], key=f"llm_model_{prov}")
        if key:
            st.success(t("llm_on", lang))
    return (key or None), model, prov


# ---------------------------------------------------------------- cache
@st.cache_resource
def _store():
    return OrderedDict()


def _cached_run(key, fn):
    s = _store()
    if key in s:
        s.move_to_end(key)
        return s[key], True
    res = fn()
    s[key] = res
    while len(s) > 12:
        s.popitem(last=False)
    return res, False


# ---------------------------------------------------------------- data tab
def _numeric_columns(df):
    out = []
    for c in df.columns:
        x = pd.to_numeric(df[c], errors="coerce")
        if x.notna().mean() >= 0.5:
            out.append(c)
    return out


def data_tab(lang, params):
    src = st.radio(t("source", lang), ["example", "upload"], horizontal=True,
                   format_func=lambda s: t("src_example" if s == "example" else "src_upload", lang))
    is_ex = src == "example"
    if is_ex:
        df, tag = dio.load_example(), "ex"
    else:
        up = st.file_uploader(t("upload", lang), type=["csv", "xlsx"], help=t("upload_help", lang))
        if up is None:
            return None
        try:
            df = dio.read_table(up.name, up.getvalue())
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
            return None
        tag = f"up_{up.name}_{up.size}"
    with st.expander(t("preview", lang), expanded=False):
        st.dataframe(df.head(50), width="stretch")

    num = _numeric_columns(df)
    if not num:
        st.error(t("non_numeric", lang))
        return None
    text_cols = [c for c in df.columns if c not in num]
    none = t("none", lang)
    c1, c2 = st.columns(2)
    with c1:
        opts = [none] + list(df.columns)
        idx = opts.index("nome") if is_ex else (opts.index(text_cols[0]) if text_cols else 0)
        name_col = st.selectbox(t("name_col", lang), opts, key=f"name_{tag}", index=idx)
        name_col = None if name_col == none else name_col
    with c2:
        first_n = st.number_input(t("first_n", lang), 0, len(df), 30 if is_ex else 0, key=f"fn_{tag}")
    crit_default = dio.EXAMPLE_CRITERIA if is_ex else [c for c in num if c != name_col][:N_MAX]
    criteria = st.multiselect(t("criteria", lang), [c for c in num if c != name_col], default=crit_default,
                              key=f"crit_{tag}")

    st.markdown(f"**{t('crit_setup', lang)}**")
    st.caption(t("crit_setup_help", lang))
    b, c = t("benefit", lang), t("cost", lang)
    base = pd.DataFrame({t("col_criterion", lang): criteria, t("col_direction", lang): [b] * len(criteria),
                         t("col_weight", lang): [None] * len(criteria), t("col_max", lang): [None] * len(criteria)})
    if is_ex and criteria == dio.EXAMPLE_CRITERIA:
        base[t("col_weight", lang)] = dio.EXAMPLE_WEIGHTS
        base[t("col_max", lang)] = dio.EXAMPLE_MAX_SCORES
    base[t("col_weight", lang)] = base[t("col_weight", lang)].astype(float)
    base[t("col_max", lang)] = base[t("col_max", lang)].astype(float)
    ed = st.data_editor(base, hide_index=True, width="stretch", key=f"ed_{tag}_{'|'.join(criteria)}_{lang}",
                        disabled=[t("col_criterion", lang)],
                        column_config={t("col_direction", lang): st.column_config.SelectboxColumn(options=[b, c], required=True),
                                       t("col_weight", lang): st.column_config.NumberColumn(min_value=0.0, format="%.4f"),
                                       t("col_max", lang): st.column_config.NumberColumn(min_value=0.0)})
    cost_all = (ed[t("col_direction", lang)] == c).values

    c3, c4 = st.columns(2)
    with c3:
        ropts = [none] + [x for x in num if x not in criteria]
        ref_col = st.selectbox(t("ref_col", lang), ropts, key=f"ref_{tag}",
                               index=ropts.index("nota") if is_ex and "nota" in ropts else 0)
        ref_col = None if ref_col == none else ref_col
    with c4:
        ref_is_rank = st.radio(t("ref_type", lang), ["score", "rank"], horizontal=True, key=f"rt_{tag}",
                               format_func=lambda s: t("ref_score" if s == "score" else "ref_rank", lang),
                               disabled=ref_col is None) == "rank"
    if ref_col:
        st.caption(t("ref_note", lang))

    # validation and preparation
    if len(criteria) < 2:
        st.warning(t("need_two", lang))
        return None
    P = dio.prepare_matrix(df, criteria, name_col, first_n or None, extra_cols=(ref_col,))
    keep = [criteria.index(k) for k in P["criteria"]]
    wcol, mcol = ed[t("col_weight", lang)].values.astype(float), ed[t("col_max", lang)].values.astype(float)
    weights = max_scores = None
    ok = True
    if np.isfinite(wcol).any():
        if not (np.isfinite(wcol).all() and (wcol > 0).all()):
            st.error(t("weights_bad", lang)); ok = False
        else:
            weights = wcol[keep]
    if np.isfinite(mcol).any():
        if not (np.isfinite(mcol).all() and (mcol > 0).all()):
            st.error(t("max_bad", lang)); ok = False
        else:
            max_scores = mcol[keep]
    m, n = P["X"].shape
    if P["excluded"]:
        st.warning(t("excluded", lang, k=P["excluded"]))
    if P["constant"]:
        st.info(t("constant", lang, c=", ".join(P["constant"])))
    if n < 2 or m < 3:
        st.warning(t("need_two", lang)); ok = False
    if m > M_MAX or n > N_MAX:
        st.error(t("too_big", lang, M=M_MAX, N=N_MAX)); ok = False
    elif m > M_WARN:
        st.warning(t("big_warn", lang, m=m))
    if not ok:
        return None
    st.success(t("summary_data", lang, m=m, n=n))

    cost = cost_all[keep]
    ref = P["frame"][ref_col].astype(float).values if ref_col else None
    h = dio.data_hash(P["X"], P["names"], P["criteria"], cost)
    key = json.dumps([h, params.to_dict(), None if weights is None else list(weights),
                      None if max_scores is None else list(max_scores),
                      None if ref is None else list(ref), ref_is_rank], default=str)
    setup = dict(X=P["X"], names=P["names"], criteria=P["criteria"], cost=cost, weights=weights,
                 max_scores=max_scores, ref=ref, ref_col=ref_col, ref_is_rank=ref_is_rank, name_col=name_col,
                 first_n=int(first_n), excluded=P["excluded"], n_initial=P["n_initial"], constant=P["constant"],
                 data_hash=h, source="example:ruf2026.csv" if is_ex else tag[3:], key=key)

    if st.button(t("run", lang), type="primary"):
        bar = st.progress(0.0)
        t0 = time.time()
        res, hit = _cached_run(key, lambda: analyze(
            P["X"], P["names"], P["criteria"], cost, params, weights, max_scores, ref, ref_is_rank,
            progress=lambda f, K: bar.progress(min(f, 1.0), text=t("running", lang, K=K))))
        bar.empty()
        st.session_state.update(res=res, setup=setup, params=params, figs={})
        st.success(t("cached", lang) if hit else t("done", lang, s=time.time() - t0))
    return setup


def _check(lang, setup):
    if "res" not in st.session_state:
        st.info(t("no_results", lang))
        return None
    if setup is not None and setup["key"] != st.session_state.setup["key"]:
        st.warning(t("stale", lang))
    return st.session_state.res


def _rename(df, lang):
    return df.rename(columns={k: ml(k, lang) for k in df.columns})


def _fmt_theta(th, lang):
    s = "; ".join(f"{x:.3f}" for x in th)
    return s.replace(".", ",") if lang == "pt" else s


def _alert_text(lang, a):
    return t(a[1], lang, **a[2])


# ---------------------------------------------------------------- SARC tab
def sarc_tab(lang, setup):
    res = _check(lang, setup)
    if res is None:
        return
    r = res["runs"][res["Kmax"]]
    st.markdown(f"**{t('status', lang)}:** {t('st_' + r['status'], lang)} · "
                + t("grid_info", lang, K=res["Kmax"], n=r["n_nodes"], s=r["n_signatures"], c=r["n_critical"]))
    if "best" not in r:
        for a in res["alerts"]:
            st.error(_alert_text(lang, a))
        return
    b = r["best"]
    c = st.columns(4)
    c[0].metric(t("area", lang), f"{b['P']:.4f}", help=t("area_help", lang))
    c[1].metric("S_min", f"{b['Smin']:.4f}", help=t("smin_help", lang))
    c[2].metric("S_mean", f"{b['Smean']:.4f}", help=t("smean_help", lang))
    c[3].metric("ρ", f"{b['rho']:.3e}", help=t("rho_help", lang))
    st.markdown(f"**{t('theta', lang)}:** ({_fmt_theta(b['theta'], lang)})")
    T = res["tables"]
    a1, a2, a3, a4 = st.tabs([t("ranking_tab", lang), t("regions_tab", lang), t("conv_tab", lang), t("weights_tab", lang)])
    with a1:
        st.dataframe(_rename(T["ranking"], lang), hide_index=True, width="stretch")
    with a2:
        st.caption(t("regions_note", lang))
        st.dataframe(T["regions"], hide_index=True, width="stretch")
    with a3:
        st.dataframe(T["convergence"], hide_index=True, width="stretch")
    with a4:
        st.dataframe(_rename(T["weights"], lang), hide_index=True, width="stretch")


# ---------------------------------------------------------------- comparison tab
def comp_tab(lang, setup):
    res = _check(lang, setup)
    if res is None or "methods" not in res:
        return
    s = st.session_state.setup
    T = res["tables"]
    st.caption(t("comp_note", lang, v=st.session_state.params.vikor_v,
                 w=t("w_norm" if s["weights"] is not None else "w_equal", lang)))
    if res.get("comparator_msgs"):
        st.warning(t("comp_msg", lang))
    st.subheader(t("ranks_all", lang))
    st.dataframe(_rename(T["ranking"].drop(columns=["S_SARC"]), lang), hide_index=True, width="stretch")
    st.subheader(t("agreement", lang))
    if "agreement" in T:
        st.info(t("ref_note", lang))
        ag = T["agreement"].copy()
        ag["method"] = ag["method"].map(lambda k: ml(k, lang))
        st.dataframe(ag, hide_index=True, width="stretch")
        st.markdown(f"**{t('largest_shifts', lang)}**")
        sh = T["largest_shifts"].copy()
        sh["method"] = sh["method"].map(lambda k: ml(k, lang))
        st.dataframe(sh, hide_index=True, width="stretch")
    else:
        st.caption(t("agreement_none", lang))
    st.subheader(t("method_corr", lang))
    mc = T["method_correlation"].copy()
    mc["method"] = mc["method"].map(lambda k: ml(k, lang))
    st.dataframe(_rename(mc, lang).style.format(precision=3), hide_index=True, width="stretch")


# ---------------------------------------------------------------- diagnostics tab
def diag_tab(lang, setup):
    res = _check(lang, setup)
    if res is None:
        return
    st.subheader(t("alerts", lang))
    if not res["alerts"]:
        st.success(t("no_alerts", lang))
    for a in res["alerts"]:
        {"error": st.error, "warning": st.warning, "info": st.info}[a[0]](_alert_text(lang, a))
    c = res.get("convergence") or {}
    if c.get("available"):
        st.subheader(t("conv_title", lang, a=c["K_low"], b=c["K_high"]))
        k = st.columns(3)
        k[0].metric(t("same_sig", lang), t("yes" if c["same_signature"] else "no", lang))
        k[1].metric(t("theta_shift", lang), f"{c['theta_shift']:.4f}",
                    delta=t("alert", lang) if c["theta_alert"] else None, delta_color="inverse")
        k[2].metric(t("area_diff", lang), f"{c['area_diff']:.4f}",
                    delta=t("alert", lang) if c["area_alert"] else None, delta_color="inverse")
    if "identifiability" in res:
        idf = res["identifiability"]
        st.subheader(t("ident_title", lang))
        k = st.columns(3)
        k[0].metric(t("cos", lang), f"{idf['cos_psi_gmd']:.4f}")
        k[1].metric(t("psi_dev", lang), f"{idf['psi_dev']:.4f}")
        k[2].metric("ρ", f"{res['runs'][res['Kmax']]['best']['rho']:.3e}")
    st.dataframe(res["tables"].get("convergence"), hide_index=True, width="stretch")


# ---------------------------------------------------------------- figures
FIG_FILES = dict(a="a_ternary_regions.png", b="b_slopegraph.png", c="c_weights.png", d="d_loao_taub.png",
                 e="e_criteria_correlation.png", f="f_radar.png", g="g_method_correlation.png")


def make_figure(name, res, setup, lang, gray, opt=None):
    """Returns PNG bytes (300 dpi), cached in session state."""
    cache = st.session_state.setdefault("figs", {})
    ck = (setup["key"], name, lang, gray, json.dumps(opt, default=str))
    if ck in cache:
        return cache[ck]
    import matplotlib.pyplot as plt
    r = res["runs"][res["Kmax"]]
    T = res["tables"]
    if name == "a":
        fig = plots.ternary_regions(r["map"]["theta"], r["map"]["region"], r["top_regions"], r["best"]["theta"],
                                    res["Kmax"], lang, gray)
    elif name == "b":
        cols = opt or (["REF", "SARC", "TOPSIS"] if "REF" in T["ranking"] else ["SARC", "AHPG", "TOPSIS"])
        cols = [c for c in cols if c in T["ranking"]]
        fig = plots.slopegraph(T["ranking"].sort_values(cols[0], kind="stable"), cols, lang=lang, gray=gray,
                               labels=[ml(c, lang) for c in cols])
    elif name == "c":
        cols = [c for c in ["PSI", "GMD", "AHPG", "SARC_center", "normative"] if c in T["weights"]]
        fig = plots.weight_bars(T["weights"], cols, lang, gray, labels=[ml(c, lang) for c in cols])
    elif name == "d":
        fig = plots.loao_bars(res["names"], r["best"]["loao_taus"], r["best"]["Smin"], r["best"]["Smean"], lang, gray)
    elif name == "e":
        C = T["criteria_correlation"]
        fig = plots.heatmap(C.iloc[:, 1:].values, list(C["criterion"]), lang, gray)
    elif name == "f":
        R = prepare(setup["X"], setup["cost"])["R"]
        crit = [setup["criteria"][j] for j in r["active"]]
        fig = plots.radar(R, crit, res["names"], opt, lang, gray)
    else:
        C = T["method_correlation"]
        fig = plots.heatmap(C.iloc[:, 1:].values, [ml(k, lang) for k in C["method"]], lang, gray)
    png = plots.to_png(fig, 300)
    plt.close(fig)
    cache[ck] = png
    return png


def _default_radar(res):
    order = res["tables"]["ranking"]["alternative"].tolist()
    return [res["names"].index(n) for n in order[:5]]


def plots_tab(lang, setup):
    res = _check(lang, setup)
    if res is None or "methods" not in res:
        return
    s = st.session_state.setup
    c1, c2 = st.columns(2)
    gray = c1.toggle(t("gray", lang), value=False, key="fig_gray")
    flang = c2.radio(t("fig_lang", lang), ["pt", "en"], index=0 if lang == "pt" else 1, horizontal=True,
                     format_func=lambda x: "Português" if x == "pt" else "English", key="fig_lang")
    st.session_state["fig_opts"] = (flang, gray)

    def show(name, title, opt=None, note=None):
        st.subheader(t(title, lang))
        if note:
            st.caption(t(note, lang))
        png = make_figure(name, res, s, flang, gray, opt)
        st.image(png, width=760)
        st.download_button(t("png", lang), png, FIG_FILES[name], "image/png", key=f"dl_{name}")

    show("a", "fig_a")
    avail = [c for c in res["tables"]["ranking"].columns if c not in ("alternative", "S_SARC")]
    dflt = [c for c in (["REF", "SARC", "TOPSIS"] if "REF" in avail else ["SARC", "AHPG", "TOPSIS"]) if c in avail]
    cols = st.multiselect(t("fig_b_cols", lang), avail, default=dflt, format_func=lambda k: ml(k, lang), key="slope_cols")
    st.session_state["slope_sel"] = cols
    if len(cols) >= 2:
        show("b", "fig_b", cols)
    show("c", "fig_c")
    show("d", "fig_d")
    show("e", "fig_e", note="fig_e_note")
    sel = st.multiselect(t("fig_f_sel", lang), list(range(len(res["names"]))), default=_default_radar(res),
                         max_selections=6, format_func=lambda i: res["names"][i], key="radar_sel")
    st.session_state["radar_idx"] = sel
    if sel:
        show("f", "fig_f", sel)
    show("g", "fig_g")


# ---------------------------------------------------------------- export tab
def _report(res, setup, params):
    s = setup
    setup_info = dict(source=s["source"], data_sha256=s["data_hash"], m=len(s["names"]), criteria=s["criteria"],
                      directions=["cost" if c else "benefit" for c in s["cost"]], name_column=s["name_col"],
                      first_n=s["first_n"], rows_initial=s["n_initial"], rows_excluded_missing=s["excluded"],
                      constant_columns_dropped=s["constant"],
                      normative_weights=None if s["weights"] is None else list(s["weights"]),
                      max_scores=None if s["max_scores"] is None else list(s["max_scores"]),
                      reference_column=s["ref_col"], reference_is_rank=s["ref_is_rank"])
    return dio.build_report(params.to_dict(), setup_info, summary(res))


def export_tab(lang, setup):
    res = _check(lang, setup)
    if res is None or "methods" not in res:
        return
    s, params = st.session_state.setup, st.session_state.params
    T = res["tables"]
    st.caption(t("exp_note", lang))
    st.subheader(t("exp_tables", lang))
    name = st.selectbox(t("exp_tables", lang), list(T), label_visibility="collapsed")
    st.dataframe(T[name], hide_index=True, width="stretch", height=240)
    c1, c2, c3 = st.columns(3)
    c1.download_button(t("exp_csv", lang), dio.to_csv_bytes(T[name]), f"{name}.csv", "text/csv")
    c2.download_button(t("exp_xlsx", lang), dio.to_xlsx_bytes(T), "sarc_tables.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    rep = _report(res, s, params)
    c3.download_button(t("exp_json", lang), dio.to_json_bytes(rep), "reproducibility_report.json", "application/json")
    st.divider()
    if st.button(t("exp_zip", lang)):
        flang, gray = st.session_state.get("fig_opts", (lang, False))
        figs = {}
        for n in "acdeg":
            figs[FIG_FILES[n]] = make_figure(n, res, s, flang, gray)
        cols = st.session_state.get("slope_sel") or None
        if cols is None or len(cols) >= 2:
            figs[FIG_FILES["b"]] = make_figure("b", res, s, flang, gray, cols)
        figs[FIG_FILES["f"]] = make_figure("f", res, s, flang, gray,
                                           st.session_state.get("radar_idx") or _default_radar(res))
        st.session_state["zip"] = dio.build_zip(T, figs, rep)
    if st.session_state.get("zip"):
        st.download_button(t("exp_zip_dl", lang), st.session_state["zip"], "sarc_results.zip", "application/zip",
                           type="primary")


# ---------------------------------------------------------------- AI tab
def ai_tab(lang, setup, api_key, model, provider="anthropic"):
    if not api_key:
        st.info(t("ai_off", lang))
        return
    res = _check(lang, setup)
    if res is None:
        return
    st.caption(t("ai_provider_now", lang, p=llm.PROVIDER_LABELS[provider], m=model))
    st.caption(t("ai_scope", lang))
    consent = st.checkbox(t("ai_consent", lang), value=False, key="ai_consent")
    st.caption(t("ai_disclaimer", lang))
    hist = st.session_state.setdefault("ai_hist", [])
    for msg in hist:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    q = st.text_area(t("ai_ask", lang), value=t("ai_default_q", lang) if not hist else "", key="ai_q")
    c1, c2 = st.columns([1, 1])
    if c1.button(t("ai_interpret", lang), type="primary") and q.strip():
        s = st.session_state.setup
        mat = None
        if consent:
            mat = pd.DataFrame(s["X"], columns=s["criteria"], index=s["names"]).to_csv(sep=";")
        ctx = llm.build_context(summary(res), mat)
        with st.spinner("..."):
            ans, err = llm.ask(api_key, q, ctx, hist, lang, model, provider=provider)
        if err:
            st.error(t("ai_err", lang, e=err))
        else:
            hist += [{"role": "user", "content": q}, {"role": "assistant", "content": ans}]
            st.session_state["ai_hist"] = hist[-20:]
            st.rerun()
    if c2.button(t("ai_clear", lang)):
        st.session_state["ai_hist"] = []
        st.rerun()
