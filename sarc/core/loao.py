"""Leave-one-alternative-out stability at a fixed theta."""
import numpy as np

from .preprocess import prepare, scores, tau_b
from ..params import DEFAULT


def loao(X, cost, theta, S_orig, params=DEFAULT):
    """Removes each alternative, recomputes normalization and weight vectors, scores the remaining
    alternatives at the same theta and compares with the original scores by tau-b.
    Returns (S_min, S_mean, n_undefined, taus); undefined tau-b counts as 0 in S_min and S_mean."""
    m = X.shape[0]
    taus = np.full(m, np.nan)
    for k in range(m):
        keep = np.arange(m) != k
        P = prepare(X[keep], cost, params)
        w = theta @ P["W"]
        S = scores(P["R"], w)
        taus[k] = tau_b(S_orig[keep], S)
    undefined = int(np.isnan(taus).sum())
    t = np.nan_to_num(taus, nan=0.0)
    return t.min(), t.mean(), undefined, taus
