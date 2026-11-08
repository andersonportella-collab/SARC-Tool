"""Full SARC run at one grid resolution, and over several resolutions.

Selection: among positive-area regions of maximum area P, lexicographic order on
(P, S_min, S_mean, rho). Only the max-P regions are evaluated by LOAO; this is lossless for the
lexicographic order because P is the first key. Discrete centers (no LOAO) are also computed for the
five largest regions, for display only.
"""
import numpy as np

from .preprocess import prepare, scores
from .grid import get_grid
from .regions import regions, component_stats, boundary_edges, rho_nodes
from .loao import loao
from ..params import DEFAULT


def _center(grid, Wn, acc, labs, lab, comp, eps_center):
    nodes = np.where(lab == comp)[0]
    be = boundary_edges(grid, acc, labs, comp)
    d = rho_nodes(Wn, nodes, be)
    dmax = d.max()
    ties = nodes[d >= dmax - eps_center]
    th = grid.theta[ties]
    best = ties[np.lexsort((th[:, 2], th[:, 1], th[:, 0]))[0]]
    return int(best), float(dmax), len(ties)


def run_sarc(X, cost, K, params=DEFAULT, progress=None):
    X = np.asarray(X, float)
    cost = np.asarray(cost, bool)
    P0 = prepare(X, cost, params)
    R, W3 = P0["R"], P0["W"]
    grid = get_grid(K)
    Wn, S, order, sig, crit, lab = regions(grid, R, W3, params.eps_tie)
    acc, labs, ntri = component_stats(grid, lab)
    pos = np.where(ntri > 0)[0]
    info = dict(K=K, m=X.shape[0], n_active=len(P0["J"]), n_nodes=len(sig), n_critical=int(crit.sum()),
                n_signatures=int(len(np.unique(sig))), n_components_posarea=int(len(pos)),
                w_psi=P0["W"][0], w_gmd=P0["W"][1], w_uni=P0["W"][2], active=P0["J"])
    if progress:
        progress(0.3)
    if len(pos) == 0:
        info["status"] = "no_plateau"
        return info

    # regions ranked by area (stable on component id); 1..5 = five largest, 0 = others, -1 = critical
    by_area = pos[np.argsort(-ntri[pos], kind="stable")]
    rank_of = {int(c): i + 1 for i, c in enumerate(by_area)}
    region_rank = np.array([0 if l < 0 else rank_of.get(int(l), 0) for l in lab])
    region_rank = np.where(region_rank > 5, 0, region_rank)
    region_rank = np.where(crit, -1, region_rank)
    info["top_areas"] = ntri[by_area[:5]] / K ** 2
    top_regions = []
    for c in by_area[:5]:
        node, rho, nt = _center(grid, Wn, acc, labs, lab, c, params.eps_center)
        top_regions.append(dict(comp=int(c), P=float(ntri[c] / K ** 2), cells=int(ntri[c]),
                                theta=grid.theta[node], rho=rho, sig=int(sig[node]), node=node))
    info["top_regions"] = top_regions
    info["map"] = dict(theta=grid.theta, region=region_rank)

    pmax = ntri[pos].max()
    cands = pos[ntri[pos] == pmax]
    res = []
    for i, c in enumerate(cands):
        node, dmax, nt = _center(grid, Wn, acc, labs, lab, c, params.eps_center)
        theta = grid.theta[node]
        Sc = scores(R, theta @ W3)
        smin, smean, und, taus = loao(X, cost, theta, Sc, params)
        res.append(dict(comp=int(c), P=float(ntri[c] / K ** 2), cells=int(ntri[c]), Smin=float(smin),
                        Smean=float(smean), rho=dmax, theta=theta, node=node, sig=int(sig[node]),
                        loao_undefined=und, n_ties_center=nt, loao_taus=taus))
        if progress:
            progress(0.3 + 0.7 * (i + 1) / len(cands))
    key = lambda r: (r["P"], r["Smin"], r["Smean"], r["rho"])
    res.sort(key=key, reverse=True)
    b = res[0]
    amb = [r for r in res[1:] if all(abs(x - y) <= params.eps_ambig for x, y in zip(key(r), key(b)))]
    info.update(status="ambiguous" if amb else "valid", best=b, n_cands=len(res), n_equiv=len(amb),
                candidates=res, ranking=order[b["node"]].copy(), S_center=scores(R, b["theta"] @ W3),
                w_center=b["theta"] @ W3)
    return info


def run_sarc_multi(X, cost, params=DEFAULT, progress=None):
    """Runs SARC for every K in params.K_list. progress(fraction, K) is optional."""
    Ks = list(params.K_list)
    out = {}
    for i, K in enumerate(Ks):
        cb = (lambda f, i=i, K=K: progress((i + f) / len(Ks), K)) if progress else None
        out[K] = run_sarc(X, cost, K, params, cb)
    return out


def fixed_configurations(X, cost, params=DEFAULT):
    """SARC scores at fixed theta: pure PSI, pure GMD, uniform and barycentric mixture."""
    P0 = prepare(X, cost, params)
    th = dict(PSI=(1, 0, 0), GMD=(0, 1, 0), UNI=(0, 0, 1), BARY=(1 / 3, 1 / 3, 1 / 3))
    return {k: scores(P0["R"], np.array(v) @ P0["W"]) for k, v in th.items()}
