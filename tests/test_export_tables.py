"""Exported tables: alerts, convergence deltas between resolutions and agreement with the SARC ranking.
Expected values are taken from the computed result itself (consistency checks), never hard coded."""
import io
import json
import zipfile
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.stats import kendalltau

from sarc import data_io as dio
from sarc.analysis import analyze, summary, alerts_table, ALERT_COLUMNS, CONVERGENCE_EXTRA, AGREEMENT_COLUMNS
from sarc.metrics import rank_desc
from sarc.params import DEFAULT

COLS = dio.EXAMPLE_CRITERIA
COST = np.zeros(5, bool)


@pytest.fixture(scope="module")
def top30():
    return dio.load_example().iloc[:30]


@pytest.fixture(scope="module")
def res30(top30):
    X = top30[COLS].values.astype(float)
    return analyze(X, top30["nome"].tolist(), COLS, COST, weights=dio.EXAMPLE_WEIGHTS,
                   max_scores=dio.EXAMPLE_MAX_SCORES, ref=top30["nota"].values)


@pytest.fixture(scope="module")
def res_theta_alert(top30):
    """Short run (K = 50, 100) with a tiny theta shift threshold, so the theta alert fires."""
    X = top30[COLS].values.astype(float)
    p = replace(DEFAULT, K_list=(50, 100), theta_shift_alert=1e-6)
    return analyze(X, top30["nome"].tolist(), COLS, COST, params=p)


def test_alerts_table_matches_collected_alerts(res30):
    A = res30["tables"]["alerts"]
    assert list(A.columns) == ALERT_COLUMNS
    assert set(A["code"]) == {a[1] for a in res30["alerts"]}
    assert "al_psi_uniform" in set(A["code"])
    assert A["message_en"].map(lambda s: isinstance(s, str) and len(s) > 0).all()
    assert not A["message_en"].str.contains("—").any()


def test_convergence_extra_columns(res30):
    C = res30["tables"]["convergence"]
    conv = res30["convergence"]
    old = ["K", "status", "nodes", "critical", "signatures", "regions_pos_area"]
    assert list(C.columns[:len(old)]) == old
    assert list(C.columns[-len(CONVERGENCE_EXTRA):]) == CONVERGENCE_EXTRA
    hi = C[C["K"] == conv["K_high"]].iloc[0]
    assert hi["theta_shift_vs_prev_K"] == conv["theta_shift"]
    assert hi["area_diff_vs_prev_K"] == conv["area_diff"]
    assert hi["same_signature_vs_prev_K"] == conv["same_signature"]
    assert hi["theta_alert"] == conv["theta_alert"] and hi["area_alert"] == conv["area_alert"]
    others = C[C["K"] != conv["K_high"]]
    assert others[CONVERGENCE_EXTRA].isna().all().all()


def test_method_agreement_against_sarc(res30):
    M = res30["tables"]["method_agreement"]
    methods = res30["methods"]
    assert list(M.columns) == AGREEMENT_COLUMNS
    assert sorted(M["method"]) == sorted(k for k in methods if k != "SARC")
    assert M["method"].is_unique and "SARC" not in set(M["method"])
    assert M["tau_b"].between(-1, 1).all()
    for k in ("TOPSIS", "AHPG"):
        exp = kendalltau(rank_desc(methods["SARC"]), rank_desc(methods[k]), variant="b").statistic
        assert M.set_index("method").loc[k, "tau_b"] == pytest.approx(exp, abs=1e-12)


def test_method_agreement_exists_without_reference(res_theta_alert):
    assert "agreement" not in res_theta_alert["tables"]
    assert len(res_theta_alert["tables"]["method_agreement"]) == len(res_theta_alert["methods"]) - 1


def test_theta_alert_row(res_theta_alert):
    A = res_theta_alert["tables"]["alerts"]
    row = A[A["code"] == "al_theta"]
    assert len(row) == 1
    assert row["value"].iloc[0] > row["threshold"].iloc[0]
    C = res_theta_alert["tables"]["convergence"]
    assert C[C["K"] == 100]["theta_alert"].iloc[0] is True


def test_summary_alert_objects_and_codes(res30):
    s = summary(res30)
    assert s["alerts_codes"] == [a[1] for a in res30["alerts"]]
    assert [a["code"] for a in s["alerts"]] == s["alerts_codes"]
    assert all(set(a) == {"level", "code", "value", "threshold"} for a in s["alerts"])
    assert len(s["method_agreement"]) == len(res30["tables"]["method_agreement"])
    back = json.loads(dio.to_json_bytes(s))
    assert back["alerts_codes"] == s["alerts_codes"]


def test_exports_with_new_tables(res30):
    T = res30["tables"]
    rep = dio.build_report(DEFAULT.to_dict(), {}, summary(res30))
    z = zipfile.ZipFile(io.BytesIO(dio.build_zip(T, {}, rep)))
    names = z.namelist()
    assert "tables/alerts.csv" in names and "tables/method_agreement.csv" in names
    conv = pd.read_csv(io.BytesIO(z.read("tables/convergence.csv")), sep=";", encoding="utf-8-sig")
    assert set(CONVERGENCE_EXTRA) <= set(conv.columns)
    xl = pd.read_excel(io.BytesIO(dio.to_xlsx_bytes(T)), sheet_name=None)
    assert {"alerts", "method_agreement"} <= set(xl)


def test_exports_with_empty_alerts(res30):
    T = dict(res30["tables"], alerts=alerts_table([]))
    assert len(T["alerts"]) == 0 and list(T["alerts"].columns) == ALERT_COLUMNS
    dio.to_xlsx_bytes(T)
    z = zipfile.ZipFile(io.BytesIO(dio.build_zip(T, {}, {"tool": "SARC-Tool"})))
    head = z.read("tables/alerts.csv").decode("utf-8-sig").strip()
    assert head == ";".join(ALERT_COLUMNS)
