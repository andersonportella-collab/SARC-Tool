# SARC-Tool: User Manual

**Version:** 1.0.0 · **Date:** November 2026 · **INPI registration:** [BR XXXXXXXX-X] · **License:** MIT
**Code:** https://github.com/andersonportella-collab/SARC-Tool · **Support:** andersonportella@yahoo.com.br

## 1. Purpose

SARC-Tool runs SARC (Stability-guided Adaptive Ranking Configuration) on a decision matrix (alternatives in
rows, criteria in columns). SARC combines three data-driven weight vectors (PSI, GMD and uniform), explores all
their mixtures on a simplex grid and selects the configuration whose constant-ranking region has the largest
area and the highest stability when alternatives are removed (LOAO). The app also computes TOPSIS, VIKOR,
COPRAS and AHP-Gaussian for comparison. Audience: researchers and multi-criteria decision analysts.

## 2. Data input

### 2.1 Format

One row per alternative and one column per criterion, with a header row. CSV (separator `;` or `,`, decimal `,`
or `.`, detected automatically) or XLSX (first sheet). Example:

| name | cost | quality | lead_time |
|---|---|---|---|
| A | 120 | 8.5 | 30 |
| B | 95 | 7.0 | 45 |

### 2.2 Steps in the Data tab

1. Choose the built-in example or upload a file.
2. Select the name column (optional) and the criteria columns (only numeric columns are listed).
3. In the setup table, set each criterion direction: **benefit** (larger is better) or **cost** (smaller is
   better). Normative weights and maximum scores are optional and apply only to TOPSIS, VIKOR and COPRAS. Fill
   all or none.
4. Optional: use only the first N rows; choose a reference column (score or position).
5. Click **Run analysis**.

### 2.3 Automatic handling

- Rows with any missing value in the criteria (or in the reference) are excluded. No imputation. The app reports
  how many rows were removed and warns that exclusion may bias the analysis.
- Constant columns are dropped and listed.
- Cost criteria use 1/x in the normalization. A cost column with zeros uses the frozen extension: 1/√q for the q
  zeros and 0 for the others.
- Public version limits: 300 alternatives and 30 criteria. For larger matrices, run locally.

## 3. Parameters

Frozen defaults (sidebar, "Advanced parameters"): K = 50, 100 and 200; critical node tolerance 1e-10; active
criterion tolerance 1e-12; center tie tolerance 1e-15; ambiguity 1e-12; VIKOR v = 0.5; τ-b with average ranks.
Changes are recorded in the JSON report. The main result uses the largest K.

## 4. Results

### 4.1 SARC tab

- **Area P**: fraction of the simplex covered by the selected region (grid cell count).
- **S_min and S_mean**: minimum and mean τ-b between the original ranking and the ranking recomputed without each
  alternative. Values close to 1 mean a stable ranking.
- **ρ**: distance from the center to the region boundary in effective weight space.
- **θ**: mixing coefficients (PSI; GMD; uniform) at the center.
- Tables: SARC ranking with all method positions, five largest regions, results per K and weight vectors.

### 4.2 Comparison tab

Positions by method, agreement with the reference (Spearman, τ-b, top 1, 3 and 5 coincidence, shifts) and method
correlation. The reference is not ground truth, and agreement does not measure quality.

### 4.3 Diagnostics tab

Alerts (never exclude results): critical nodes, ambiguous selection, signature change between resolutions,
θ shift > 0.015, area difference > 0.01, PSI practically uniform, collinearity of w^PSI − u and w^GMD − u, small
ρ, two or fewer active criteria.

### 4.4 Charts tab

(a) ternary map of the five largest regions with the center; (b) slopegraph of positions across methods;
(c) weight vectors; (d) LOAO τ-b by removed alternative; (e) criteria correlation heat map; (f) radar chart of
normalized profiles; (g) method correlation heat map. Grayscale and label language are configurable. Each figure
can be downloaded as PNG 300 dpi.

### 4.5 Export tab

CSV for each table, XLSX with all tables, JSON reproducibility report (parameters, versions, SHA-256 data hash,
timestamp) and a ZIP with tables, figures and report.

### 4.6 AI interpretation (optional)

Off by default. Typing an Anthropic API key in the sidebar shows the interpretation tab. Only the result summary
is sent; the matrix is sent only if you tick the consent box. The key is not stored. AI answers may contain errors.

## 5. Step by step example

1. Open the app; the RUF 2026 example is preselected with the first 30 rows, criteria ens, pes, mer, ino, int
   (benefit), weights 0.32, 0.42, 0.18, 0.04, 0.04, maximum scores 32, 42, 18, 4, 4 and reference `nota`.
2. Click Run analysis (a few seconds).
3. Expected result (K = 200): P = 0.3622; S_min = 0.9754; S_mean = 0.9947; θ = (0.335; 0.320; 0.345); no
   critical nodes; same signature at K = 50, 100 and 200. Alert: PSI practically uniform.
4. Against the published score: SARC Spearman 0.866 and τ-b 0.692; TOPSIS 0.992 and 0.949; COPRAS 0.9996 and 0.995.

## 6. Method limitations

The core is ordinally equivalent to a weighted sum; the area is a cell count; the center is discrete; θ is weakly
identifiable when PSI ≈ uniform. The app does not claim SARC is superior.

## 7. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| No numeric column | unusual decimal or separator | save as CSV with `;` and decimal `,`, or XLSX |
| Many rows excluded | missing values | review the sheet; the app does not impute |
| Unexpected result | benefit/cost direction swapped | review the Direction column |
| AHP-Gaussian missing | zero in a cost criterion | 1/x is undefined; review the data |
| Matrix above the limit | more than 300 rows or 30 criteria | use first N rows or run locally |

## 8. Reference and contact

Methodological article: in preparation. Authors: Anderson Gonçalves Portella (UFF), Carlos Francisco Simões Gomes
(UFF), Marcos dos Santos (Brazilian Naval War College). Support: andersonportella@yahoo.com.br.
