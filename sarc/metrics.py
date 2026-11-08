"""Agreement metrics between a method and a reference ranking (the reference is not ground truth)."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau, rankdata


def rank_desc(s):
    """Positions with average ranks for ties; larger score = better = position 1."""
    return rankdata(-np.asarray(s, float), method="average")


def agreement(ref_score, s, names=None, n_largest=5):
    rr, rs = rank_desc(ref_score), rank_desc(s)
    sp = spearmanr(rr, rs).statistic
    kt = kendalltau(rr, rs, variant="b").statistic
    disp = np.abs(rr - rs)
    top = {k: len(set(np.argsort(rr, kind="stable")[:k]) & set(np.argsort(rs, kind="stable")[:k]))
           for k in (1, 3, 5)}
    idx = np.argsort(-disp, kind="stable")[:n_largest]
    names = np.arange(1, len(s) + 1).astype(str) if names is None else np.asarray(names)
    largest = [dict(alternative=str(names[i]), ref_pos=float(rr[i]), method_pos=float(rs[i]),
                    shift=float(rs[i] - rr[i])) for i in idx]
    return dict(spearman=float(sp), tau_b=float(kt), top1=top[1], top3=top[3], top5=top[5],
                disp_mean=float(disp.mean()), disp_max=float(disp.max()), largest=largest)


def agreement_table(ref_score, methods, names=None):
    rows, shifts = [], []
    for k, v in methods.items():
        a = agreement(ref_score, v, names)
        for L in a.pop("largest"):
            shifts.append(dict(method=k, **L))
        rows.append(dict(method=k, **a))
    return pd.DataFrame(rows), pd.DataFrame(shifts)


def method_correlation(methods):
    """Spearman correlation between the rankings of all methods."""
    keys = list(methods)
    M = np.array([rank_desc(methods[k]) for k in keys])
    C = np.corrcoef(M)  # Pearson on ranks = Spearman
    return pd.DataFrame(C, index=keys, columns=keys)


def ranks_table(methods, names, ref_score=None, ref_label="REF"):
    tab = pd.DataFrame({"alternative": names})
    if ref_score is not None:
        tab[ref_label] = rank_desc(ref_score)
    for k, v in methods.items():
        tab[k] = rank_desc(v)
    return tab
