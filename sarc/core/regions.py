"""Node scores, critical nodes, constant-ranking regions, area by cell count, boundary and radius."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from .preprocess import scores
from ..params import DEFAULT


def regions(grid, R, W3, eps_tie=DEFAULT.eps_tie):
    """Returns effective weights, node scores, orders, signature ids, critical mask and component
    labels (-1 for critical nodes)."""
    Wn = grid.theta @ W3
    S = scores(R, Wn)
    order = np.argsort(-S, axis=1, kind="stable")
    Ss = np.take_along_axis(S, order, axis=1)
    crit = (np.abs(np.diff(Ss, axis=1)) <= eps_tie).any(1)
    _, sig = np.unique(order, axis=0, return_inverse=True)
    sig = sig.ravel()
    e = grid.edges
    ok = (~crit[e[:, 0]]) & (~crit[e[:, 1]]) & (sig[e[:, 0]] == sig[e[:, 1]])
    N = len(sig)
    A = coo_matrix((np.ones(ok.sum()), (e[ok, 0], e[ok, 1])), shape=(N, N))
    _, lab = connected_components(A, directed=False)
    lab = np.where(crit, -1, lab)
    return Wn, S, order, sig, crit, lab


def component_stats(grid, lab):
    """Elementary triangles fully inside a component (area by cell count)."""
    tri = grid.tri
    l0, l1, l2 = lab[tri[:, 0]], lab[tri[:, 1]], lab[tri[:, 2]]
    acc = (l0 >= 0) & (l0 == l1) & (l1 == l2)
    labs = l0[acc]
    ntri = np.bincount(labs, minlength=lab.max() + 1)
    return acc, labs, ntri


def boundary_edges(grid, acc, labs, comp):
    T = grid.tri[acc][labs == comp]
    E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [0, 2]]])
    E = np.sort(E, axis=1)
    key = E[:, 0] * (len(grid.P) + 1) + E[:, 1]
    u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    once = cnt[inv.ravel()] == 1
    return E[once]


def rho_nodes(Wn, nodes, bedges, chunk=96):
    """Distance, in effective weight space, from each node to the region boundary polyline."""
    A = Wn[bedges[:, 0]]
    B = Wn[bedges[:, 1]]
    AB = B - A
    AB2 = (AB ** 2).sum(1)
    AB2s = np.where(AB2 > 0, AB2, 1.0)
    out = np.empty(len(nodes))
    for s in range(0, len(nodes), chunk):
        w = Wn[nodes[s:s + chunk]]
        d = w[:, None, :] - A[None]
        t = np.clip((d * AB[None]).sum(2) / AB2s[None], 0, 1)
        t = np.where(AB2[None] > 0, t, 0.0)
        diff = d - t[:, :, None] * AB[None]
        out[s:s + chunk] = np.sqrt((diff ** 2).sum(2)).min(1)
    return out
