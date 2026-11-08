"""Cost criteria (frozen zero extension), comparators with cost, input handling and export."""
import io
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from sarc.core import normalize, prepare, run_sarc
from sarc.comparators import topsis, vikor, copras, ahp_gaussian, run_comparators
from sarc.data_io import read_table, prepare_matrix, build_zip, build_report, to_xlsx_bytes
from sarc.metrics import rank_desc


def test_cost_without_zeros_uses_reciprocal():
    x = np.array([[1.0], [2.0], [4.0]])
    R = normalize(x, [True])
    inv = 1 / x[:, 0]
    assert np.allclose(R[:, 0], inv / np.linalg.norm(inv))


def test_cost_with_zeros_frozen_extension():
    x = np.array([[0.0], [3.0], [0.0], [5.0]])
    R = normalize(x, [True])
    assert np.allclose(R[:, 0], [1 / np.sqrt(2), 0, 1 / np.sqrt(2), 0])
    assert np.isclose(np.linalg.norm(R[:, 0]), 1.0)


def test_cost_with_single_zero():
    R = normalize(np.array([[2.0], [0.0], [1.0]]), [True])
    assert np.allclose(R[:, 0], [0, 1, 0])


def test_sarc_runs_with_cost_zero_column():
    rng = np.random.default_rng(1)
    X = rng.uniform(1, 10, (25, 4))
    X[[2, 7], 3] = 0.0
    r = run_sarc(X, [False, False, True, True], 50)
    assert r["status"] in ("valid", "ambiguous")
    assert len(r["ranking"]) == 25


def test_comparators_cost_equivalence():
    rng = np.random.default_rng(2)
    X = rng.uniform(1, 10, (12, 3))
    w = np.array([0.5, 0.3, 0.2])
    Xn = X.copy()
    Xn[:, 2] = 20 - X[:, 2]          # reversed copy: benefit on 20-x vs cost on x
    a = vikor(X, w, 0.5, [False, False, True])
    b = vikor(Xn, w, 0.5, None)
    assert np.allclose(a, b)
    s = topsis(X, w, [False, False, True])
    assert s.shape == (12,) and np.all((s >= 0) & (s <= 1))
    q = copras(X, w, [False, False, True])
    assert np.isfinite(q).all()
    # COPRAS with benefit criteria only is a weighted sum of sum-normalized columns
    assert np.allclose(copras(X, w), (w * X / X.sum(0)).sum(1))


def test_ahp_gaussian_cost_and_zero_guard():
    X = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 5.0]])
    s, w = ahp_gaussian(X, [False, True])
    assert np.isclose(w.sum(), 1)
    X[0, 1] = 0
    with pytest.raises(ValueError):
        ahp_gaussian(X, [False, True])
    out, wg, msgs = run_comparators(X, [False, True])
    assert "AHPG" not in out and msgs


def test_read_csv_semicolon_decimal_comma():
    raw = "nome;c1;c2\nA;1,5;2\nB;2,5;3\n".encode("utf-8")
    df = read_table("x.csv", raw)
    assert df["c1"].tolist() == [1.5, 2.5]


def test_read_xlsx_roundtrip():
    df = pd.DataFrame({"n": ["a", "b"], "x": [1.0, 2.0]})
    back = read_table("t.xlsx", to_xlsx_bytes({"s": df}))
    pd.testing.assert_frame_equal(back, df, check_dtype=False)


def test_prepare_matrix_constant_missing_first_n():
    df = pd.DataFrame({"nome": list("ABCDE"), "c1": [1, 2, None, 4, 5], "c2": [7, 7, 7, 7, 7],
                       "c3": [5, 4, 3, 2, 1]})
    p = prepare_matrix(df, ["c1", "c2", "c3"], "nome")
    assert p["constant"] == ["c2"] and p["criteria"] == ["c1", "c3"]
    assert p["excluded"] == 1 and p["names"] == ["A", "B", "D", "E"]
    p2 = prepare_matrix(df, ["c1", "c3"], "nome", first_n=2)
    assert p2["X"].shape == (2, 2) and p2["excluded"] == 0


def test_zip_export():
    tab = {"t": pd.DataFrame({"a": [1, 2]})}
    rep = build_report({"K": [50]}, {}, {})
    z = zipfile.ZipFile(io.BytesIO(build_zip(tab, {"f.png": b"\x89PNG"}, rep)))
    names = z.namelist()
    assert "tables/t.csv" in names and "figures/f.png" in names and "reproducibility_report.json" in names
    assert json.loads(z.read("reproducibility_report.json"))["tool"] == "SARC-Tool"


def test_rank_desc_average_ties():
    assert rank_desc([3, 1, 3]).tolist() == [1.5, 3.0, 1.5]
