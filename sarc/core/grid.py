"""Regular grid of the 2-simplex of mixing coefficients theta = (a, b, c) = (p, q, K-p-q)/K."""
from functools import lru_cache
import numpy as np


class Grid:
    def __init__(self, K):
        self.K = K
        idx = -np.ones((K + 1, K + 1), int)
        P, Q = [], []
        for p in range(K + 1):
            for q in range(K - p + 1):
                idx[p, q] = len(P)
                P.append(p)
                Q.append(q)
        self.idx = idx
        self.P = np.array(P)
        self.Q = np.array(Q)
        self.Rr = K - self.P - self.Q
        self.theta = np.stack([self.P, self.Q, self.Rr], 1) / K
        e = []
        for p in range(K + 1):
            for q in range(K - p + 1):
                i = idx[p, q]
                if p + 1 + q <= K:
                    e.append((i, idx[p + 1, q]))
                if p + q + 1 <= K:
                    e.append((i, idx[p, q + 1]))
                if q - 1 >= 0 and p + 1 + q - 1 <= K:
                    e.append((i, idx[p + 1, q - 1]))
        self.edges = np.array(e)
        t = []
        for p in range(K):
            for q in range(K - p):
                t.append((idx[p, q], idx[p + 1, q], idx[p, q + 1]))
                if p + q + 2 <= K:
                    t.append((idx[p + 1, q], idx[p, q + 1], idx[p + 1, q + 1]))
        self.tri = np.array(t)
        assert len(self.tri) == K * K


@lru_cache(maxsize=8)
def get_grid(K):
    return Grid(int(K))
