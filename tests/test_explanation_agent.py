"""Unit tests for ExplanationAgent fallback mode and mocked LLM adapter mode."""

import pytest
from agents.explanation_agent import (
    ExplanationAgent,
    FallbackExplanationAdapter,
    BaseLLMAdapter,
    FALLBACK_EXPLANATION,
)
from pipeline.investigator import run_investigation


class MockLLMAdapter(BaseLLMAdapter):
    """Mock adapter that records prompt and returns fixed response without external API calls."""

    def __init__(self):
        self.last_prompt = None

    def generate_explanation(self, prompt: str) -> str:
        self.last_prompt = prompt
        return "Mocked AI explanation report based strictly on supplied evidence."


def test_fallback_mode_without_api_key(monkeypatch):
    """Verifies that ExplanationAgent defaults to FallbackExplanationAdapter when LLM_API_KEY is unset."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    agent = ExplanationAgent()

    assert isinstance(agent.adapter, FallbackExplanationAdapter)

    result = run_investigation("cluster_a_overload")
    explanation = agent.generate_explanation(result)

    assert explanation == FALLBACK_EXPLANATION
    assert "Cluster A is overloaded" in explanation
    assert "Cluster B remained healthy" in explanation


def test_mocked_model_mode_does_not_make_external_api_calls():
    """Verifies that ExplanationAgent works with a custom/mock adapter without external network calls."""
    mock_adapter = MockLLMAdapter()
    agent = ExplanationAgent(adapter=mock_adapter)

    result = run_investigation("cluster_a_overload")
    explanation = agent.generate_explanation(result)

    assert explanation == "Mocked AI explanation report based strictly on supplied evidence."
    assert mock_adapter.last_prompt is not None
    assert "cluster-a" in mock_adapter.last_prompt
    assert "cluster-a overload caused by GPU saturation" in mock_adapter.last_prompt
    assert "100.0%" in mock_adapter.last_prompt


def test_agent_accepts_dictionary_input():
    """Verifies that ExplanationAgent accepts dictionary structured inputs as well as InvestigationResult."""
    mock_adapter = MockLLMAdapter()
    agent = ExplanationAgent(adapter=mock_adapter)

    dict_data = {
        "affected_cluster": "cluster-a",
        "root_cause": "cluster-a overload caused by GPU saturation",
        "confidence": 95.0,
        "evidence": [],
        "recommendation": "shift traffic to cluster-b",
    }
    explanation = agent.generate_explanation(dict_data)

    assert explanation == "Mocked AI explanation report based strictly on supplied evidence."
    assert "cluster-a" in mock_adapter.last_prompt


def test_agent_raises_error_on_invalid_input_type():
    """Verifies that ExplanationAgent raises TypeError when invalid input types are provided."""
    agent = ExplanationAgent()
    with pytest.raises(TypeError):
        agent.generate_explanation("invalid string input")
