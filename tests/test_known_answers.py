"""Known-answer tests: RUF 2026, first 30 rows, criteria ens, pes, mer, ino, int (all benefit)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sarc.core import prepare, run_sarc
from sarc.comparators import ahp_gaussian
from sarc.analysis import analyze
from sarc.data_io import load_example, EXAMPLE_CRITERIA as COLS, EXAMPLE_WEIGHTS, EXAMPLE_MAX_SCORES

HERE = Path(__file__).parent
COST = np.zeros(5, bool)


@pytest.fixture(scope="module")
def ruf():
    return load_example()


@pytest.fixture(scope="module")
def top30(ruf):
    return ruf.iloc[:30]


@pytest.fixture(scope="module")
def X30(top30):
    return top30[COLS].values.astype(float)


@pytest.fixture(scope="module")
def res30(top30, X30):
    return analyze(X30, top30["nome"].tolist(), COLS, COST, weights=EXAMPLE_WEIGHTS,
                   max_scores=EXAMPLE_MAX_SCORES, ref=top30["nota"].values)


def test_normalized_columns_unit_norm(X30):
    R = prepare(X30, COST)["R"]
    assert np.allclose(np.sqrt((R ** 2).sum(0)), 1.0, atol=1e-14)


def test_weight_vectors(X30):
    W = prepare(X30, COST)["W"]
    assert np.allclose(W[0], [0.2017, 0.2022, 0.1999, 0.1988, 0.1973], atol=5e-5)
    assert np.allclose(W[1], [0.1412, 0.1073, 0.1958, 0.2574, 0.2982], atol=5e-5)


def test_ahp_gaussian_matches_web_app_and_R(X30):
    _, w = ahp_gaussian(X30)
    assert np.allclose(w, [0.13457, 0.10241, 0.21647, 0.25140, 0.29516], atol=5e-6)


def test_sarc_K200(res30):
    r = res30["runs"][200]
    b = r["best"]
    assert r["n_nodes"] == 20301
    assert r["n_signatures"] == 14
    assert r["n_critical"] == 0
    assert b["cells"] == 14487 and b["P"] == pytest.approx(0.362175, abs=1e-9)
    assert np.allclose(b["theta"], [0.335, 0.320, 0.345], atol=1e-12)
    assert b["rho"] == pytest.approx(1.6485e-4, rel=1e-3)
    assert b["Smin"] == pytest.approx(0.97537, abs=1e-5)
    assert b["Smean"] == pytest.approx(0.99475, abs=1e-5)
    assert r["status"] == "valid"


def test_sarc_K100_K50_and_convergence(res30):
    r100, r50 = res30["runs"][100], res30["runs"][50]
    assert r100["best"]["P"] == pytest.approx(0.3577, abs=1e-4)
    assert np.allclose(r100["best"]["theta"], [0.33, 0.33, 0.34], atol=1e-12)
    assert r50["best"]["P"] == pytest.approx(0.3476, abs=1e-4)
    assert np.allclose(r50["best"]["theta"], [0.32, 0.34, 0.34], atol=1e-12)
    c = res30["convergence"]
    assert c["same_signature"] and c["same_signature_all"]
    assert not c["theta_alert"] and not c["area_alert"]


def test_region_map_matches_reference(res30):
    ref = pd.read_csv(HERE / "top30_K200_regioes.csv", sep=";")
    mp = res30["runs"][200]["map"]
    assert (ref["regiao_por_area"].values == mp["region"]).all()
    assert np.allclose(ref[["a_PSI", "b_GMD", "c_UNIFORME"]].values, mp["theta"], atol=1e-12)
    node = res30["runs"][200]["best"]["node"]
    assert ref["centro_selecionado"].values[node] == 1


@pytest.mark.parametrize("method,sp,tb", [("SARC", 0.8661, 0.6920), ("AHPG", 0.8447, 0.6736),
                                          ("TOPSIS", 0.9920, 0.9494), ("VIKOR", 0.9466, 0.8299),
                                          ("COPRAS", 0.9996, 0.9954)])
def test_agreement_with_published(res30, method, sp, tb):
    ag = res30["tables"]["agreement"].set_index("method")
    assert ag.loc[method, "spearman"] == pytest.approx(sp, abs=6e-5)
    assert ag.loc[method, "tau_b"] == pytest.approx(tb, abs=6e-5)


def test_identifiability_flags_psi_uniform(res30):
    assert res30["identifiability"]["psi_uniform"]
    assert "al_psi_uniform" in [a[1] for a in res30["alerts"]]


def test_top50_K200(ruf):
    X = ruf.iloc[:50][COLS].values.astype(float)
    b = run_sarc(X, COST, 200)["best"]
    assert b["P"] == pytest.approx(0.0671, abs=1e-4)
    assert b["Smin"] == pytest.approx(0.9915, abs=1e-4)
    assert np.allclose(b["theta"], [0.195, 0.600, 0.205], atol=1e-12)


def test_complete_cases_K200(ruf):
    X = ruf[ruf[COLS].notna().all(axis=1)][COLS].values.astype(float)
    assert len(X) == 180
    b = run_sarc(X, COST, 200)["best"]
    assert b["P"] == pytest.approx(0.0384, abs=1e-4)
    assert b["Smin"] == pytest.approx(0.9987, abs=1e-4)
    assert np.allclose(b["theta"], [0.32, 0.19, 0.49], atol=6e-3)


def test_scale_invariance(X30):
    f = np.array([3.7, 0.01, 1000, 12.5, 0.2])
    a, b = prepare(X30, COST), prepare(X30 * f, COST)
    assert np.abs(a["R"] - b["R"]).max() < 1e-15
    assert np.abs(a["W"] - b["W"]).max() < 1e-15
    sa, sb = run_sarc(X30, COST, 100), run_sarc(X30 * f, COST, 100)
    assert (sa["ranking"] == sb["ranking"]).all()
    assert np.abs(sa["best"]["theta"] - sb["best"]["theta"]).max() == 0
    assert sa["best"]["P"] == sb["best"]["P"]
