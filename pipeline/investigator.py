"""Main investigation pipeline orchestrator for MantisGuard."""

from typing import Optional
from analysis.schemas import InvestigationResult
from simulator.telemetry_generator import get_all_telemetry
from analysis.detector import detect_all_anomalies
from analysis.correlator import build_timeline
from analysis.root_cause import investigate_root_cause
from analysis.confidence import calculate_confidence
from recommendation.recommender import calculate_cluster_health, generate_recommendation
from agents.explanation_agent import ExplanationAgent


def run_investigation(scenario_name: str = "cluster_a_overload") -> InvestigationResult:
    """Executes end-to-end investigation pipeline on simulated telemetry data.

    1. Load scenario telemetry.
    2. Validate telemetry data models.
    3. Detect anomalies across telemetry metrics.
    4. Correlate anomalous events into a unified chronological timeline.
    5. Score root cause probabilities per cluster.
    6. Calculate confidence score (0-100%).
    7. Compute cluster operational health statuses.
    8. Generate traffic remediation recommendation.
    9. Generate natural language incident explanation.
    10. Return structured InvestigationResult contract.
    """
    # 1 & 2. Load and validate scenario telemetry
    baseline_metrics, metrics, logs, traces = get_all_telemetry(scenario_name)

    # 3. Anomaly Detection
    anomalies = detect_all_anomalies(metrics, baseline_metrics)

    # 4. Event Correlation & Timeline
    timeline = build_timeline(anomalies, logs, traces)

    # 5. Root Cause Scoring
    root_cause_res = investigate_root_cause(metrics, baseline_metrics, logs, traces)
    affected_cluster = root_cause_res["affected_cluster"]
    root_cause = root_cause_res["root_cause"]
    evidence = root_cause_res["evidence"]
    scores = root_cause_res["scores"]

    # 6. Confidence Engine
    confidence = calculate_confidence(
        affected_cluster=affected_cluster,
        root_cause_result=root_cause_res,
        metrics=metrics,
        logs=logs,
        traces=traces,
        anomalies=anomalies,
    )

    # 7. Cluster Health Comparison
    cluster_health_list = calculate_cluster_health(metrics, root_cause_scores=scores)

    # 8. Recommendation Generation
    recommendation = generate_recommendation(
        affected_cluster=affected_cluster,
        root_cause=root_cause,
        health_list=cluster_health_list,
    )

    # 9. AI Explanation Agent
    agent = ExplanationAgent()
    explanation_data = {
        "affected_cluster": affected_cluster,
        "root_cause": root_cause,
        "confidence": confidence,
        "evidence": evidence,
        "recommendation": recommendation,
    }
    explanation = agent.generate_explanation(explanation_data)

    # Determine title & severity based on investigation findings
    top_score = scores.get(affected_cluster, 0.0)
    if top_score >= 50.0:
        incident_title = f"CRITICAL: Inference Latency Spike & GPU Overload on {affected_cluster}"
        severity = "CRITICAL"
    elif top_score > 0.0:
        incident_title = f"WARNING: Minor Performance Degradation on {affected_cluster}"
        severity = "WARN"
    else:
        incident_title = "INFO: Nominal AI Cluster Operations"
        severity = "INFO"

    # 10. Return complete InvestigationResult contract
    return InvestigationResult(
        incident_title=incident_title,
        severity=severity,
        affected_cluster=affected_cluster,
        root_cause=root_cause,
        confidence=confidence,
        evidence=evidence,
        correlated_timeline=timeline,
        cluster_health=cluster_health_list,
        recommendation=recommendation,
        explanation=explanation,
    )
