"""Frozen default parameters of SARC-Tool. Changing them changes results; the app shows them and
records them in the reproducibility report."""
from dataclasses import dataclass, asdict, field


@dataclass(frozen=True)
class SarcParams:
    K_list: tuple = (50, 100, 200)      # simplex grid resolutions; selection reported at max(K_list)
    eps_tie: float = 1e-10              # critical node tolerance (score tie between consecutive positions)
    tol_active: float = 1e-12           # active criterion tolerance (relative range)
    eps_gmd: float = 1e-15              # GMD degeneracy guard
    eps_center: float = 1e-15           # tie tolerance for the discrete center (max distance to boundary)
    eps_ambig: float = 1e-12            # ambiguity tolerance in the lexicographic key
    vikor_v: float = 0.5                # VIKOR strategy weight
    theta_shift_alert: float = 0.015    # convergence alert, ||theta_K100 - theta_K200||
    area_diff_alert: float = 0.01       # convergence alert, |P_K100 - P_K200|
    rho_small_alert: float = 1e-3       # identifiability alert when rho is below this value
    psi_uniform_alert: float = 0.02     # PSI considered practically uniform when max|w_psi - u| * n < this

    def to_dict(self):
        d = asdict(self)
        d["K_list"] = list(self.K_list)
        d["tau_b"] = "Kendall tau-b with average ranks (scipy.stats.kendalltau, variant='b')"
        return d


DEFAULT = SarcParams()

# Size limits for the public version
M_WARN = 200
M_MAX = 300
N_MAX = 30
