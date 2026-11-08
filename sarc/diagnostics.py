"""Diagnostics: convergence between resolutions, critical nodes, ambiguity, identifiability.
All flags are alerts, never exclusions. Messages are keys translated in sarc.i18n."""
import numpy as np

from .params import DEFAULT


def convergence(runs, params=DEFAULT):
    Ks = sorted(runs)
    if len(Ks) < 2:
        return {}
    Kh, Kl = Ks[-1], Ks[-2]
    a, b = runs[Kl], runs[Kh]
    if "best" not in a or "best" not in b:
        return dict(K_low=Kl, K_high=Kh, available=False)
    out = dict(K_low=Kl, K_high=Kh, available=True,
               same_signature=bool((a["ranking"] == b["ranking"]).all()),
               theta_shift=float(np.linalg.norm(a["best"]["theta"] - b["best"]["theta"])),
               area_diff=float(abs(a["best"]["P"] - b["best"]["P"])))
    out["same_signature_all"] = bool(all("ranking" in runs[K] and (runs[K]["ranking"] == b["ranking"]).all()
                                         for K in Ks))
    out["theta_alert"] = out["theta_shift"] > params.theta_shift_alert
    out["area_alert"] = out["area_diff"] > params.area_diff_alert
    return out


def identifiability(w_psi, w_gmd, rho=None, n_active=None, params=DEFAULT):
    n = len(w_psi)
    u = np.full(n, 1 / n)
    a, b = w_psi - u, w_gmd - u
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    cos = float(abs(a @ b) / (na * nb)) if na > 0 and nb > 0 else 1.0
    psi_dev = float(np.abs(a).max() * n)
    return dict(cos_psi_gmd=cos, norm_psi_u=float(na), norm_gmd_u=float(nb), psi_dev=psi_dev,
                psi_uniform=psi_dev < params.psi_uniform_alert,
                collinear=cos > 0.999,
                rho_small=(rho is not None and rho < params.rho_small_alert),
                few_active=(n_active is not None and n_active <= 2))


def collect_alerts(runs, params=DEFAULT):
    """Returns list of (level, i18n_key, format_kwargs)."""
    K = max(runs)
    r = runs[K]
    al = []
    if r.get("status") == "no_plateau":
        al.append(("error", "al_no_plateau", {}))
        return al
    for k in sorted(runs):
        if runs[k]["n_critical"] > 0:
            al.append(("warning", "al_critical", dict(K=k, n=runs[k]["n_critical"])))
    if r["status"] == "ambiguous":
        al.append(("warning", "al_ambiguous", dict(n=r["n_equiv"])))
    c = convergence(runs, params)
    if c.get("available"):
        if not c["same_signature"]:
            al.append(("warning", "al_signature", dict(a=c["K_low"], b=c["K_high"])))
        if c["theta_alert"]:
            al.append(("warning", "al_theta", dict(v=c["theta_shift"], t=params.theta_shift_alert)))
        if c["area_alert"]:
            al.append(("warning", "al_area", dict(v=c["area_diff"], t=params.area_diff_alert)))
    idf = identifiability(r["w_psi"], r["w_gmd"], r["best"]["rho"], r["n_active"], params)
    if idf["psi_uniform"]:
        al.append(("info", "al_psi_uniform", dict(v=idf["psi_dev"])))
    if idf["collinear"]:
        al.append(("warning", "al_collinear", dict(v=idf["cos_psi_gmd"])))
    if idf["rho_small"]:
        al.append(("warning", "al_rho", dict(v=r["best"]["rho"])))
    if idf["few_active"]:
        al.append(("warning", "al_few_active", dict(n=r["n_active"])))
    if r["best"]["loao_undefined"] > 0:
        al.append(("info", "al_loao_undef", dict(n=r["best"]["loao_undefined"])))
    return al
