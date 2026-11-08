# SARC-Tool

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-red)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![INPI](https://img.shields.io/badge/INPI-BR%20XXXXXXXX--X-orange)]()

**Stability-guided Adaptive Ranking Configuration.** A web application that runs SARC on a decision matrix
uploaded by the user, compares it with TOPSIS, VIKOR, COPRAS and AHP-Gaussian, and exports tables, charts
and a reproducibility report.

Leia em português: [README_PT.md](README_PT.md)

## Access

Online app: *https://sarc-tool.streamlit.app/*

## What it does

1. **Input**: CSV or XLSX upload, or the built-in example (Folha University Ranking 2026, reduced). Choose the
   name column, the criteria and the direction of each one (benefit or cost). Constant columns are dropped and
   listed. Missing data are never imputed: only complete cases are used, the number of excluded rows is shown,
   with a warning that exclusion may bias results. Optionally use only the first N rows.
2. **SARC**: vector normalization, PSI, GMD and uniform weight vectors, regular grid of the mixing simplex at
   K = 50, 100, 200, critical nodes, constant-ranking regions, area P by grid cell count, boundary, radius ρ,
   discrete center, LOAO stability (S_min, S_mean), lexicographic selection (P, S_min, S_mean, ρ) and ambiguity
   test.
3. **Comparators**: TOPSIS, VIKOR (v = 0.5), COPRAS (optional normative weights, optional rescaling of each
   column to 0 to 100 by its maximum possible score) and AHP-Gaussian (port of the R code). Fixed SARC
   configurations: pure PSI, pure GMD, uniform and barycentric mixture.
4. **Reference (optional)**: Spearman, Kendall τ-b, top 1, 3 and 5 coincidence, mean and maximum position shift,
   five largest shifts. The reference is a comparison context, not ground truth.
5. **Diagnostics**: convergence between the two largest K (signature, θ shift > 0.015, area difference > 0.01, as
   alerts only), critical nodes, ambiguity, identifiability (collinearity of w^PSI − u and w^GMD − u, small ρ,
   two or fewer active criteria, PSI practically uniform).
6. **Charts** (matplotlib, PT or EN labels, optional grayscale, PNG 300 dpi): ternary map of the five largest
   regions, slopegraph of positions, weight vectors, LOAO τ-b, criteria correlation heat map, radar chart of
   normalized profiles, method correlation heat map.
7. **Export**: CSV, XLSX (all tables), JSON reproducibility report (parameters, library versions, SHA-256 data
   hash, timestamp) and a ZIP with everything.
8. **Optional AI interpretation**: off by default. It turns on only when the user picks a provider, Anthropic
   (Claude) or OpenAI (ChatGPT), and types the API key in the sidebar. Only the result summary is sent; the decision matrix is sent only with explicit consent.

## Limitations (also shown in the app)

- The core is ordinally equivalent to a weighted sum: at each θ, the ranking is that of a weighted sum of (1 − r_ij)².
- Area P is measured by grid cell count. The center is a grid node.
- When PSI is practically uniform, θ is weakly identifiable.
- The app does not claim SARC is superior to other methods.

## Frozen defaults

| Parameter | Value |
|---|---|
| Grid resolutions K | 50, 100, 200 |
| Critical node tolerance | 1e-10 |
| Active criterion tolerance | 1e-12 |
| Center tie tolerance | 1e-15 |
| Ambiguity tolerance | 1e-12 |
| VIKOR v | 0.5 |
| τ-b | average ranks |

Public version limits: up to 300 alternatives and 30 criteria (warning above 200 alternatives).

## Local installation

```bash
git clone https://github.com/andersonportella-collab/SARC-Tool.git
cd SARC-Tool
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
streamlit run app.py
```

## Tests

```bash
pytest -q
```

The suite reproduces the article's known answers (RUF 2026, first 30 rows): PSI, GMD and AHP-Gaussian weights,
SARC at K = 50, 100 and 200 (20,301 nodes, 14 signatures, P = 0.362175, θ = (0.335; 0.320; 0.345)), agreement
with the published ranking for every method, the Top 50 and 180 complete-case subsets, scale invariance, the
frozen zero extension for cost criteria, input handling, export and an app smoke test.

## Code structure

```
app.py                 Streamlit entry point
sarc/core/             SARC numerical core (no Streamlit): preprocess, grid, regions, loao, engine
sarc/comparators.py    TOPSIS, VIKOR, COPRAS, AHP-Gaussian (benefit and cost)
sarc/metrics.py        Agreement metrics
sarc/diagnostics.py    Convergence, identifiability, alerts
sarc/analysis.py       End-to-end pipeline and result tables
sarc/plots.py          Figures
sarc/data_io.py        Reading, preparation, export
sarc/llm.py            Optional AI interpretation
sarc/i18n.py           PT/EN strings
sarc/meta.py           Authors, citation, INPI and article placeholders
sarc/ui/               Interface components and tabs
tests/                 pytest suite
docs/                  User manuals (PT, EN) and deployment guide
```

## Authors

- **Anderson Gonçalves Portella**, Fluminense Federal University (UFF), [ORCID 0000-0001-6520-4301](https://orcid.org/0000-0001-6520-4301)
- **Carlos Francisco Simões Gomes**, Fluminense Federal University (UFF), [ORCID 0000-0002-6865-0275](https://orcid.org/0000-0002-6865-0275)
- **Marcos dos Santos**, Brazilian Naval War College (EGN), [ORCID 0000-0003-1533-5535](https://orcid.org/0000-0003-1533-5535)

## How to cite

Portella, A. G., Gomes, C. F. S., & Santos, M. (2026). *SARC-Tool: Stability-guided Adaptive Ranking
Configuration* (Version 1.0.0) [Computer software]. INPI [BR XXXXXXXX-X].
https://github.com/andersonportella-collab/SARC-Tool

Article: in preparation (the reference will be added after publication). See also [CITATION.cff](CITATION.cff).

## Support

andersonportella@yahoo.com.br

## License

MIT. See [LICENSE](LICENSE).
