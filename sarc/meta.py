"""Identity, authors, citation. Edit the placeholders below when the article and the INPI registration
are available."""
from . import __version__

APP_NAME = "SARC-Tool"
YEAR = 2026
VERSION = __version__
REPO_URL = "https://github.com/andersonportella-collab/SARC-Tool"
APP_URL = "https://sarc-tool.streamlit.app/"                   
SUPPORT_EMAIL = "andersonportella@yahoo.com.br"
INPI = "[BR512026010417-3]"            # replace with the registration number

# Article citation: keep None until publication, then fill the dict below.
ARTICLE = None
# ARTICLE = dict(authors_abnt="PORTELLA, A. G.; GOMES, C. F. S.; SANTOS, M.",
#                authors_apa="Portella, A. G., Gomes, C. F. S., & Santos, M.",
#                title="...", journal="...", volume="...", number="...", pages="...", year=2027, doi="10....")

INSTITUTIONS = {
    "UFF": {"pt": "Universidade Federal Fluminense (UFF)", "en": "Fluminense Federal University (UFF)"},
    "EGN": {"pt": "Escola de Guerra Naval (EGN)", "en": "Brazilian Naval War College (EGN)"},
}

AUTHORS = [
    dict(name="Anderson Gonçalves Portella", inst="UFF", orcid="0000-0001-6520-4301"),
    dict(name="Prof. Dr. Carlos Francisco Simões Gomes", inst="UFF", orcid="0000-0002-6865-0275"),
    dict(name="Prof. Dr. Marcos dos Santos", inst="EGN", orcid="0000-0003-1533-5535"),
]


def software_citation(lang):
    t = {"pt": "SARC-Tool: Configuração Adaptativa de Ranking Guiada por Estabilidade. Software, versão",
         "en": "SARC-Tool: Stability-Guided Adaptive Ranking Configuration. Software, version"}[lang]
    inst = "; ".join(INSTITUTIONS[k][lang] for k in ("UFF", "EGN"))
    abnt = (f"PORTELLA, A. G.; GOMES, C. F. S.; SANTOS, M. **{t} {VERSION}**. {inst}, {YEAR}. "
            f"Registro INPI: {INPI}. Disponível em: {REPO_URL}.")
    apa = (f"Portella, A. G., Gomes, C. F. S., & Santos, M. ({YEAR}). *{t} {VERSION}* [Computer software]. "
           f"{inst}. INPI {INPI}. {REPO_URL}")
    bib = ("@software{portella" + str(YEAR) + "sarctool,\n"
           "  author = {Portella, Anderson Gon{\\c{c}}alves and Gomes, Carlos Francisco Sim{\\~o}es and Santos, Marcos dos},\n"
           f"  title = {{SARC-Tool: Stability-guided Adaptive Ranking Configuration}},\n"
           f"  version = {{{VERSION}}},\n  year = {{{YEAR}}},\n  url = {{{REPO_URL}}},\n"
           f"  note = {{INPI: {INPI}}}\n}}")
    return abnt, apa, bib


def article_citation():
    if not ARTICLE:
        return None
    a = ARTICLE
    abnt = (f"{a['authors_abnt']}. {a['title']}. **{a['journal']}**, v. {a['volume']}, n. {a['number']}, "
            f"p. {a['pages']}, {a['year']}. DOI: {a['doi']}.")
    apa = (f"{a['authors_apa']} ({a['year']}). {a['title']}. *{a['journal']}*, {a['volume']}({a['number']}), "
           f"{a['pages']}. https://doi.org/{a['doi']}")
    return abnt, apa
