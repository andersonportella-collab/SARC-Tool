"""TOPSIS, VIKOR, COPRAS and AHP-Gaussian with benefit and cost criteria.
Scores are returned so that larger = better (VIKOR returns -Q). With benefit criteria only, the
results are identical to the reference comparators.py used in the article experiment."""
import numpy as np


def _cost(cost, n):
    return np.zeros(n, bool) if cost is None else np.asarray(cost, bool)


def topsis(X, w, cost=None):
    X = np.asarray(X, float)
    c = _cost(cost, X.shape[1])
    R = X / np.sqrt((X ** 2).sum(0))
    V = R * w
    ip = np.where(c, V.min(0), V.max(0))
    im = np.where(c, V.max(0), V.min(0))
    dp = np.sqrt(((V - ip) ** 2).sum(1))
    dm = np.sqrt(((V - im) ** 2).sum(1))
    return dm / (dp + dm)


def vikor(X, w, v=0.5, cost=None):
    X = np.asarray(X, float)
    c = _cost(cost, X.shape[1])
    f_best = np.where(c, X.min(0), X.max(0))
    f_worst = np.where(c, X.max(0), X.min(0))
    span = np.abs(f_best - f_worst)
    rng = np.where(span > 0, span, 1.0)
    T = w * np.abs(f_best - X) / rng
    S, Rr = T.sum(1), T.max(1)

    def nz(a):
        d = a.max() - a.min()
        return (a - a.min()) / d if d > 0 else np.zeros_like(a)

    Q = v * nz(S) + (1 - v) * nz(Rr)
    return -Q


def copras(X, w, cost=None):
    """Q_i = S+_i + sum(S-) / (S-_i * sum(1/S-)). With benefit criteria only, Q_i = S+_i."""
    X = np.asarray(X, float)
    c = _cost(cost, X.shape[1])
    D = w * X / X.sum(0)
    Sp = D[:, ~c].sum(1)
    if not c.any():
        return Sp
    Sm = D[:, c].sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = np.where(Sm > 0, 1.0 / Sm, np.inf)
        add = Sm.sum() * inv / inv[np.isfinite(inv)].sum() if np.isfinite(inv).any() else np.zeros_like(Sm)
    return Sp + add


def ahp_gaussian(X, cost=None):
    """Port of ahpgaussian.default.R: cost criteria use 1/x, sum normalization, factor = sd/mean
    (sample sd). Returns (global scores, criteria weights). Raises ValueError when a cost criterion has
    zeros (1/x undefined, as in the R code)."""
    X = np.asarray(X, float).copy()
    c = _cost(cost, X.shape[1])
    if c.any():
        if (X[:, c] == 0).any():
            raise ValueError("AHP-Gaussian undefined: zero value in a cost criterion")
        X[:, c] = 1.0 / X[:, c]
    N = X / X.sum(0)
    mean = N.mean(0)
    sd = N.std(0, ddof=1)
    factor = sd / mean
    wts = factor / factor.sum()
    return N @ wts, wts


def rescale(X, max_scores):
    """Rescales each column to 0..100 dividing by the maximum possible score (when given)."""
    X = np.asarray(X, float)
    if max_scores is None:
        return X
    ms = np.asarray(max_scores, float)
    return X / ms * 100


def run_comparators(X, cost, weights=None, max_scores=None, v=0.5):
    """Runs the four comparators. weights: normative weights for TOPSIS/VIKOR/COPRAS (equal weights when
    None). Returns (scores dict, ahp_weights or None, messages list)."""
    X = np.asarray(X, float)
    n = X.shape[1]
    w = np.full(n, 1 / n) if weights is None else np.asarray(weights, float) / np.sum(weights)
    Xr = rescale(X, max_scores)
    out, msgs = {}, []
    out["TOPSIS"] = topsis(Xr, w, cost)
    out["VIKOR"] = vikor(Xr, w, v, cost)
    out["COPRAS"] = copras(Xr, w, cost)
    wg = None
    try:
        out["AHPG"], wg = ahp_gaussian(Xr, cost)
    except ValueError as e:
        msgs.append(str(e))
    return out, wg, msgs
