"""Active criteria, vector normalization (benefit/cost with frozen zero extension), PSI/GMD/uniform
weight vectors and SARC scores. Numerically identical to the reference sarc_core.py."""
import numpy as np
from scipy.stats import kendalltau

from ..params import DEFAULT


def active_cols(X, tol=DEFAULT.tol_active):
    rng = X.max(0) - X.min(0)
    scale = np.maximum(1.0, np.abs(X).max(0))
    return np.where(rng > tol * scale)[0]


def normalize(X, cost):
    """Vector normalization. Cost criteria use 1/x; a cost column with q >= 1 zeros uses the frozen
    extension: 1/sqrt(q) for the zeros and 0 for the other entries."""
    m, n = X.shape
    R = np.zeros_like(X, dtype=float)
    for j in range(n):
        x = X[:, j].astype(float)
        if cost[j]:
            q = int((x == 0).sum())
            if q >= 1:
                R[:, j] = np.where(x == 0, 1 / np.sqrt(q), 0.0)
                continue
            x = 1.0 / x
        R[:, j] = x / np.sqrt((x ** 2).sum())
    return R


def weight_vectors(R, eps_gmd=DEFAULT.eps_gmd):
    m, n = R.shape
    rbar = R.mean(0)
    V = ((R - rbar) ** 2).sum(0)
    phi = 1 - V
    wpsi = phi / phi.sum() if phi.sum() > 0 else np.full(n, 1 / n)
    Rs = np.sort(R, axis=0)
    coef = (2 * np.arange(m) - m + 1)[:, None]
    G = 2.0 / (m * (m - 1)) * (coef * Rs).sum(0)
    wgmd = G / G.sum() if G.sum() > eps_gmd else np.full(n, 1 / n)
    u = np.full(n, 1 / n)
    return wpsi, wgmd, u


def prepare(X, cost, params=DEFAULT):
    X = np.asarray(X, float)
    cost = np.asarray(cost, bool)
    J = active_cols(X, params.tol_active)
    R = normalize(X[:, J], cost[J])
    wpsi, wgmd, u = weight_vectors(R, params.eps_gmd)
    return dict(J=J, R=R, W=np.vstack([wpsi, wgmd, u]))


def scores(R, w):
    """S = 1 - D, D = sqrt(sum_j w_j (1 - r_ij)^2); w: (n,) or (N, n) -> (m,) or (N, m)."""
    H = (1 - R) ** 2
    D = np.sqrt(np.clip(np.atleast_2d(w) @ H.T, 0, None))
    S = 1 - D
    return S[0] if np.ndim(w) == 1 else S


def tau_b(a, b):
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return np.nan
    return kendalltau(a, b, variant="b").statistic
