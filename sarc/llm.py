"""Optional interpretation of results by an LLM (Anthropic Claude or OpenAI ChatGPT). Disabled unless the
user types an API key. By default only the result summary is sent; the decision matrix is sent only with
explicit consent. No Streamlit imports."""
import json

PROVIDERS = ("anthropic", "openai")
PROVIDER_LABELS = {"anthropic": "Anthropic (Claude)", "openai": "OpenAI (ChatGPT)"}
DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4o-mini"}
DEFAULT_MODEL = DEFAULT_MODELS["anthropic"]
# models that accept the server-side refusal fallback in "default" mode
_FALLBACK_MODELS = {"claude-sonnet-5-5", "claude-opus-5-5", "claude-opus-5", "claude-fable-5-1"}

SYSTEM = {
    "pt": ("Você interpreta resultados do SARC (Stability-guided Adaptive Ranking Configuration) e de "
           "métodos multicritério de comparação. Regras: não afirme que o SARC é superior a outros métodos; "
           "a referência, se houver, não é verdade de campo; mencione os limites quando pertinentes (núcleo "
           "ordinalmente equivalente a uma soma ponderada, área medida por contagem de células da malha, "
           "centro discreto, identificabilidade fraca quando PSI é praticamente uniforme). Use apenas os "
           "números fornecidos, sem inventar valores. Responda em português, de forma objetiva, sem travessões."),
    "en": ("You interpret results of SARC (Stability-guided Adaptive Ranking Configuration) and of comparison "
           "multi-criteria methods. Rules: do not claim SARC is superior to other methods; the reference, if "
           "any, is not ground truth; mention limits when relevant (core ordinally equivalent to a weighted sum, "
           "area measured by grid cell count, discrete center, weak identifiability when PSI is practically "
           "uniform). Use only the numbers provided, never invent values. Answer in English, concisely, without "
           "em dashes."),
}


def build_context(summary, matrix_csv=None):
    ctx = "RESULT SUMMARY (JSON):\n" + json.dumps(summary, ensure_ascii=False, default=lambda o: o.tolist()
                                                   if hasattr(o, "tolist") else str(o))
    if matrix_csv:
        ctx += "\n\nDECISION MATRIX (CSV, shared with user consent):\n" + matrix_csv
    return ctx


def ask(api_key, question, context, history=None, lang="pt", model=None, max_tokens=4000, provider="anthropic"):
    """Returns (answer_text, error_message). history: list of {"role", "content"} (last 20 kept)."""
    model = model or DEFAULT_MODELS[provider]
    if provider == "openai":
        return _ask_openai(api_key, question, context, history, lang, model, max_tokens)
    return _ask_anthropic(api_key, question, context, history, lang, model, max_tokens)


def _ask_openai(api_key, question, context, history, lang, model, max_tokens):
    try:
        import openai
    except ImportError:
        return None, "openai package not installed"
    client = openai.OpenAI(api_key=api_key)
    msgs = [{"role": "system", "content": SYSTEM[lang]}] + list(history or [])[-20:]
    msgs.append({"role": "user", "content": f"{context}\n\nQUESTION:\n{question}"})
    try:
        resp = client.chat.completions.create(model=model, messages=msgs, max_completion_tokens=max_tokens)
    except openai.AuthenticationError:
        return None, "auth"
    except openai.NotFoundError:
        return None, "model"
    except openai.RateLimitError:
        return None, "rate"
    except openai.APIStatusError as e:
        return None, f"API {e.status_code}"
    except openai.APIConnectionError:
        return None, "connection"
    choice = resp.choices[0]
    if getattr(choice.message, "refusal", None):
        return None, "refusal"
    return choice.message.content or "", None


def _ask_anthropic(api_key, question, context, history, lang, model, max_tokens):
    try:
        import anthropic
    except ImportError:
        return None, "anthropic package not installed"
    client = anthropic.Anthropic(api_key=api_key)
    msgs = list(history or [])[-20:]
    msgs.append({"role": "user", "content": f"{context}\n\nQUESTION:\n{question}"})
    kw = dict(model=model, max_tokens=max_tokens, system=SYSTEM[lang], messages=msgs)
    try:
        if model in _FALLBACK_MODELS:
            resp = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"],
                                               extra_body={"fallbacks": "default"}, **kw)
        else:
            resp = client.messages.create(**kw)
    except anthropic.AuthenticationError:
        return None, "auth"
    except anthropic.NotFoundError:
        return None, "model"
    except anthropic.RateLimitError:
        return None, "rate"
    except anthropic.APIStatusError as e:
        return None, f"API {e.status_code}"
    except anthropic.APIConnectionError:
        return None, "connection"
    if resp.stop_reason == "refusal":
        return None, "refusal"
    text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
    return text, None
