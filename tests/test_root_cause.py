"""Unit tests for root-cause scoring and confidence calculation."""

from simulator.telemetry_generator import get_all_telemetry
from analysis.detector import detect_all_anomalies
from analysis.root_cause import investigate_root_cause
from analysis.confidence import calculate_confidence


def test_cluster_a_receives_highest_root_cause_score():
    baseline, metrics, logs, traces = get_all_telemetry("cluster_a_overload")
    res = investigate_root_cause(metrics, baseline, logs, traces)

    assert res["affected_cluster"] == "cluster-a"
    assert "cluster-a overload" in res["root_cause"]
    assert res["scores"]["cluster-a"] == 100.0  # Max 100 points
    assert res["scores"]["cluster-b"] == 0.0


def test_confidence_staying_between_0_and_100():
    baseline, metrics, logs, traces = get_all_telemetry("cluster_a_overload")
    anomalies = detect_all_anomalies(metrics, baseline)
    res = investigate_root_cause(metrics, baseline, logs, traces)

    confidence = calculate_confidence(
        affected_cluster=res["affected_cluster"],
        root_cause_result=res,
        metrics=metrics,
        logs=logs,
        traces=traces,
        anomalies=anomalies,
    )

    assert 0.0 <= confidence <= 100.0
    assert confidence >= 90.0  # Expected high confidence for this clear scenario
