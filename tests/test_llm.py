"""LLM module with fake clients (no network): request shape, consent gating and provider routing."""
from types import SimpleNamespace

import openai
import anthropic

from sarc import llm


def test_context_excludes_matrix_without_consent():
    ctx = llm.build_context({"P": 0.36})
    assert "DECISION MATRIX" not in ctx
    assert "DECISION MATRIX" in llm.build_context({"P": 0.36}, "a;b\n1;2")


def test_openai_route(monkeypatch):
    seen = {}

    class Fake:
        def __init__(self, api_key):
            seen["key"] = api_key
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kw):
            seen.update(kw)
            msg = SimpleNamespace(content="ok openai", refusal=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    monkeypatch.setattr(openai, "OpenAI", Fake)
    ans, err = llm.ask("k", "q?", "ctx", [], "pt", None, provider="openai")
    assert (ans, err) == ("ok openai", None)
    assert seen["model"] == "gpt-4o-mini" and seen["messages"][0]["role"] == "system"
    assert seen["messages"][-1]["content"].endswith("q?")


def test_anthropic_route(monkeypatch):
    seen = {}

    class Fake:
        def __init__(self, api_key):
            self.messages = SimpleNamespace(create=self.create)
            self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

        def create(self, **kw):
            seen.update(kw)
            return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="ok claude")])

    monkeypatch.setattr(anthropic, "Anthropic", Fake)
    ans, err = llm.ask("k", "q?", "ctx", [], "en", None, provider="anthropic")
    assert (ans, err) == ("ok claude", None)
    assert seen["model"] == "claude-sonnet-5-5" and "system" in seen
