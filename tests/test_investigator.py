"""Unit tests for end-to-end investigation pipeline and fallback explanation mode."""

import os
from pipeline.investigator import run_investigation
from agents.explanation_agent import ExplanationAgent, FallbackExplanationAdapter
from analysis.schemas import InvestigationResult


def test_fallback_explanation_working_without_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    agent = ExplanationAgent()
    assert isinstance(agent.adapter, FallbackExplanationAdapter)

    report = agent.generate_explanation({})
    assert "Cluster A is overloaded" in report
    assert "Cluster B remained healthy" in report


def test_run_investigation_returns_complete_result():
    result = run_investigation("cluster_a_overload")

    assert isinstance(result, InvestigationResult)
    assert result.affected_cluster == "cluster-a"
    assert "cluster-a overload" in result.root_cause
    assert result.confidence >= 90.0
    assert len(result.evidence) > 0
    assert len(result.cluster_health) == 2
    assert result.recommendation.source_cluster == "cluster-a"
    assert result.recommendation.target_cluster == "cluster-b"
    assert "Cluster A is overloaded" in result.explanation
