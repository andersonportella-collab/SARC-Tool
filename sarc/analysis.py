"""End-to-end analysis used by the app and the tests (no Streamlit)."""
import numpy as np
import pandas as pd

from .params import DEFAULT
from .core import run_sarc_multi, fixed_configurations
from .comparators import run_comparators
from .metrics import rank_desc, agreement, agreement_table, method_correlation
from .diagnostics import convergence, identifiability, collect_alerts
from .i18n import t

ALERT_COLUMNS = ["level", "code", "value", "threshold", "message_en"]
CONVERGENCE_EXTRA = ["theta_shift_vs_prev_K", "area_diff_vs_prev_K", "same_signature_vs_prev_K",
                     "theta_alert", "area_alert"]
AGREEMENT_COLUMNS = ["method", "tau_b", "spearman", "top1", "top3", "top5", "disp_mean", "disp_max"]


def _alert_value(kw):
    """Numeric value carried by an alert: v (measured value) or n (count); None when not applicable."""
    for k in ("v", "n"):
        if k in kw:
            return kw[k]
    return None


def alert_records(alerts):
    """Alert tuples (level, code, kwargs) as dicts with level, code, value and threshold."""
    return [dict(level=lvl, code=code, value=_alert_value(kw), threshold=kw.get("t")) for lvl, code, kw in alerts]


def alerts_table(alerts):
    """One row per alert; zero rows (same columns) when there is no alert."""
    rows = [dict(rec, message_en=t(a[1], "en", **a[2])) for rec, a in zip(alert_records(alerts), alerts)]
    return pd.DataFrame(rows, columns=ALERT_COLUMNS)


def _convergence_table(rows, conv):
    """Per-K table; the comparison with the previous resolution is filled on the K_high row only."""
    df = pd.DataFrame(rows)
    for c in CONVERGENCE_EXTRA:
        df[c] = pd.Series([None] * len(df), dtype=object)
    if conv.get("available"):
        i = df.index[df["K"] == conv["K_high"]][0]
        vals = [conv["theta_shift"], conv["area_diff"], conv["same_signature"], conv["theta_alert"],
                conv["area_alert"]]
        for c, v in zip(CONVERGENCE_EXTRA, vals):
            df.at[i, c] = v
    return df


def method_agreement_table(methods, names=None):
    """Agreement of every method with the SARC ranking (tau-b, Spearman, top-k, shifts)."""
    base = methods["SARC"]
    rows = []
    for k, v in methods.items():
        if k == "SARC":
            continue
        a = agreement(base, v, names)
        a.pop("largest")
        rows.append(dict(method=k, **a))
    return pd.DataFrame(rows, columns=AGREEMENT_COLUMNS)


def analyze(X, names, criteria, cost, params=DEFAULT, weights=None, max_scores=None,
            ref=None, ref_is_rank=False, progress=None):
    X = np.asarray(X, float)
    cost = np.asarray(cost, bool)
    names = list(names)
    runs = run_sarc_multi(X, cost, params, progress)
    Kmax = max(params.K_list)
    r = runs[Kmax]
    res = dict(runs=runs, Kmax=Kmax, names=names, criteria=list(criteria), cost=cost, tables={})
    if r.get("status") == "no_plateau":
        res["alerts"] = collect_alerts(runs, params)
        res["tables"]["alerts"] = alerts_table(res["alerts"])
        return res

    methods = {"SARC": r["S_center"]}
    methods.update(fixed_configurations(X, cost, params))
    comp, wg, msgs = run_comparators(X, cost, weights, max_scores, params.vikor_v)
    methods.update(comp)
    res.update(methods=methods, ahp_weights=wg, comparator_msgs=msgs)

    T = res["tables"]
    rk = pd.DataFrame({"alternative": names, "S_SARC": r["S_center"], "SARC": rank_desc(r["S_center"])})
    for k, v in methods.items():
        if k != "SARC":
            rk[k] = rank_desc(v)
    T["ranking"] = rk.sort_values("SARC", kind="stable").reset_index(drop=True)
    T["scores"] = pd.DataFrame({"alternative": names, **{k: v for k, v in methods.items()}})

    act = r["active"]
    wt = pd.DataFrame({"criterion": [criteria[j] for j in act],
                       "direction": ["cost" if cost[j] else "benefit" for j in act],
                       "PSI": r["w_psi"], "GMD": r["w_gmd"], "UNI": r["w_uni"], "SARC_center": r["w_center"]})
    if wg is not None:
        wt["AHPG"] = wg[act]
    if weights is not None:
        wn = np.asarray(weights, float) / np.sum(weights)
        wt["normative"] = wn[act]
    T["weights"] = wt

    T["regions"] = pd.DataFrame([dict(region=i + 1, P=g["P"], cells=g["cells"], theta_PSI=g["theta"][0],
                                      theta_GMD=g["theta"][1], theta_UNI=g["theta"][2], rho=g["rho"],
                                      signature=g["sig"], selected=g["comp"] == r["best"]["comp"])
                                 for i, g in enumerate(r["top_regions"])])
    rows = []
    for K in sorted(runs):
        s = runs[K]
        row = dict(K=K, status=s["status"], nodes=s["n_nodes"], critical=s["n_critical"],
                   signatures=s["n_signatures"], regions_pos_area=s["n_components_posarea"])
        if "best" in s:
            b = s["best"]
            row.update(P=b["P"], cells=b["cells"], S_min=b["Smin"], S_mean=b["Smean"], rho=b["rho"],
                       theta_PSI=b["theta"][0], theta_GMD=b["theta"][1], theta_UNI=b["theta"][2],
                       candidates=s["n_cands"], equivalent=s["n_equiv"], loao_undefined=b["loao_undefined"],
                       center_ties=b["n_ties_center"])
        rows.append(row)
    res["convergence"] = convergence(runs, params)
    T["convergence"] = _convergence_table(rows, res["convergence"])
    T["loao"] = pd.DataFrame({"removed_alternative": names, "tau_b": r["best"]["loao_taus"]})
    T["method_correlation"] = method_correlation(methods).reset_index().rename(columns={"index": "method"})
    T["method_agreement"] = method_agreement_table(methods, names)
    T["criteria_correlation"] = (pd.DataFrame(X, columns=criteria).corr(method="spearman")
                                 .reset_index().rename(columns={"index": "criterion"}))

    if ref is not None:
        ref = np.asarray(ref, float)
        ref_score = -ref if ref_is_rank else ref
        res["ref_score"] = ref_score
        ag, sh = agreement_table(ref_score, methods, names)
        T["agreement"] = ag
        T["largest_shifts"] = sh
        rk.insert(3, "REF", rank_desc(ref_score))
        T["ranking"] = rk.sort_values("SARC", kind="stable").reset_index(drop=True)

    res["identifiability"] = identifiability(r["w_psi"], r["w_gmd"], r["best"]["rho"], r["n_active"], params)
    res["alerts"] = collect_alerts(runs, params)
    T["alerts"] = alerts_table(res["alerts"])
    return res


def summary(res):
    """Compact JSON-friendly summary (used in the report and the optional LLM context)."""
    r = res["runs"][res["Kmax"]]
    out = dict(m=r["m"], n_active=r["n_active"], status=r["status"], K=res["Kmax"],
               alerts=alert_records(res["alerts"]),          # objects: level, code, value, threshold
               alerts_codes=[a[1] for a in res["alerts"]])   # previous format, kept for compatibility
    if "best" not in r:
        return out
    b = r["best"]
    out.update(P=b["P"], S_min=b["Smin"], S_mean=b["Smean"], rho=b["rho"], theta=b["theta"],
               signatures=r["n_signatures"], critical=r["n_critical"],
               top_areas=r["top_areas"], convergence=res["convergence"], identifiability=res["identifiability"],
               top10_SARC=list(res["tables"]["ranking"]["alternative"].head(10)))
    if "agreement" in res["tables"]:
        out["agreement"] = res["tables"]["agreement"].to_dict(orient="records")
    if "method_agreement" in res["tables"]:
        out["method_agreement"] = res["tables"]["method_agreement"].to_dict(orient="records")
    return out
