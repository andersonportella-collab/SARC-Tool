"""Smoke test of the Streamlit app with the built-in example (both languages)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.mark.parametrize("lang", ["Português", "English"])
def test_app_runs_example(lang):
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception
    at.selectbox(key="lang").set_value(lang).run()
    assert not at.exception
    run = [b for b in at.button if b.label in ("Executar análise", "Run analysis")][0]
    run.click().run()
    assert not at.exception
    assert "res" in at.session_state
    r = at.session_state["res"]["runs"][200]["best"]
    assert r["cells"] == 14487
    texts = " ".join(m.value for m in at.markdown)
    assert "—" not in texts


def test_ai_tab_only_with_key():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    labels = [tb.label for tb in at.tabs]
    assert "Interpretação por IA" not in labels
    at.text_input(key="llm_key_anthropic").input("test-key-not-real").run()
    assert not at.exception
    assert "Interpretação por IA" in [tb.label for tb in at.tabs]


def test_ai_tab_with_openai_provider():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    at.radio(key="llm_provider").set_value("openai").run()
    assert at.text_input(key="llm_model_openai").value == "gpt-4o-mini"
    at.text_input(key="llm_key_openai").input("test-key-not-real").run()
    assert not at.exception
    assert "Interpretação por IA" in [tb.label for tb in at.tabs]
