"""SARC numerical core (no Streamlit imports)."""
from .preprocess import active_cols, normalize, weight_vectors, prepare, scores, tau_b
from .grid import Grid, get_grid
from .regions import regions, component_stats, boundary_edges, rho_nodes
from .loao import loao
from .engine import run_sarc, run_sarc_multi, fixed_configurations
