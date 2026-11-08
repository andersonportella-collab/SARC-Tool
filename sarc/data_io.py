"""Input reading, matrix preparation (no imputation) and export (CSV, XLSX, JSON report, ZIP).
Named data_io to avoid shadowing the standard library module io."""
import io
import csv
import json
import hashlib
import platform
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

EXAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "ruf2026.csv"
EXAMPLE_CRITERIA = ["ens", "pes", "mer", "ino", "int"]
EXAMPLE_MAX_SCORES = [32, 42, 18, 4, 4]
EXAMPLE_WEIGHTS = [0.32, 0.42, 0.18, 0.04, 0.04]


def load_example():
    return pd.read_csv(EXAMPLE_PATH, sep=";", encoding="utf-8")


def read_table(name, data: bytes):
    """Reads CSV (separator and decimal detected) or XLSX."""
    if name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(data))
    text = data.decode("utf-8-sig", errors="replace")
    try:
        sep = csv.Sniffer().sniff(text[:5000], delimiters=";,\t").delimiter
    except csv.Error:
        sep = ";" if text.count(";") > text.count(",") else ","
    dec = "," if sep == ";" and _comma_decimal(text) else "."
    return pd.read_csv(io.StringIO(text), sep=sep, decimal=dec)


def _comma_decimal(text):
    import re
    return len(re.findall(r"\d,\d", text[:5000])) > len(re.findall(r"\d\.\d", text[:5000]))


def prepare_matrix(df, criteria, name_col=None, first_n=None, extra_cols=()):
    """Selects the first N rows (optional), coerces criteria to numeric, keeps complete cases only
    (no imputation) and drops constant columns. Returns dict with X, names, kept criteria, dropped
    constant criteria, number of excluded rows and the filtered frame."""
    d = df.copy()
    if first_n:
        d = d.iloc[:int(first_n)]
    n0 = len(d)
    num = d[list(criteria)].apply(pd.to_numeric, errors="coerce")
    need = list(criteria) + [c for c in extra_cols if c]
    extra = d[[c for c in extra_cols if c]].apply(pd.to_numeric, errors="coerce") if any(extra_cols) else None
    mask = num.notna().all(axis=1)
    if extra is not None:
        mask &= extra.notna().all(axis=1)
    d, num = d[mask], num[mask]
    rng = num.max() - num.min()
    const = [c for c in criteria if not (rng[c] > 0)]
    kept = [c for c in criteria if c not in const]
    if name_col:
        names = d[name_col].astype(str).where(d[name_col].notna(), None)
        names = [n if n not in (None, "nan", "") else f"#{i + 1}" for i, n in zip(d.index, names)]
    else:
        names = [f"A{i + 1}" for i in range(len(d))]
    return dict(X=num[kept].values.astype(float), names=list(names), criteria=kept, constant=const,
                excluded=int(n0 - len(d)), n_initial=n0, frame=d.reset_index(drop=True))


def data_hash(X, names, criteria, cost):
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(X, float).tobytes())
    h.update(json.dumps([list(map(str, names)), list(criteria), list(map(bool, cost))]).encode())
    return h.hexdigest()


def lib_versions():
    import scipy, matplotlib
    v = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
             pandas=pd.__version__, matplotlib=matplotlib.__version__)
    try:
        import streamlit
        v["streamlit"] = streamlit.__version__
    except Exception:
        pass
    from . import __version__
    v["sarc_tool"] = __version__
    return v


def _json_default(o):
    if hasattr(o, "tolist"):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


def build_report(params, setup, summary):
    return dict(tool="SARC-Tool", generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                versions=lib_versions(), parameters=params, setup=setup, summary=summary)


def to_json_bytes(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False, default=_json_default).encode("utf-8")


def to_csv_bytes(df):
    return df.to_csv(index=False, sep=";").encode("utf-8-sig")


def to_xlsx_bytes(tables: dict):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        for name, df in tables.items():
            df.to_excel(w, sheet_name=str(name)[:31], index=False)
    return buf.getvalue()


def build_zip(tables: dict, figures: dict, report: dict):
    """tables: name -> DataFrame; figures: filename -> PNG bytes; report: dict."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, df in tables.items():
            z.writestr(f"tables/{name}.csv", to_csv_bytes(df))
        z.writestr("tables/all_tables.xlsx", to_xlsx_bytes(tables))
        for fn, png in figures.items():
            z.writestr(f"figures/{fn}", png)
        z.writestr("reproducibility_report.json", to_json_bytes(report))
    return buf.getvalue()
