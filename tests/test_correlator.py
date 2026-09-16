"""Unit tests for event correlator and timeline builder."""

from simulator.telemetry_generator import get_all_telemetry
from analysis.detector import detect_all_anomalies
from analysis.correlator import correlate_events, build_timeline, identify_precursor_events


def test_timeline_ordering_and_correlation():
    baseline, metrics, logs, traces = get_all_telemetry("cluster_a_overload")
    anomalies = detect_all_anomalies(metrics, baseline)

    timeline = build_timeline(anomalies, logs, traces)
    assert len(timeline) > 0

    # Ensure timeline items are strictly ordered by timestamp
    timestamps = [item["timestamp"] for item in timeline]
    assert timestamps == sorted(timestamps)


def test_correlation_of_same_cluster_events():
    baseline, metrics, logs, traces = get_all_telemetry("cluster_a_overload")
    anomalies = detect_all_anomalies(metrics, baseline)

    cluster_a_correlated = correlate_events(anomalies, logs, traces, target_cluster="cluster-a")
    assert len(cluster_a_correlated) > 0
    for item in cluster_a_correlated:
        assert item["cluster"] == "cluster-a"


def test_identify_precursor_events():
    baseline, metrics, logs, traces = get_all_telemetry("cluster_a_overload")
    anomalies = detect_all_anomalies(metrics, baseline)

    timeline = build_timeline(anomalies, logs, traces)
    precursors = identify_precursor_events(timeline)

    assert len(precursors) > 0
    # First precursor should be at the earliest timestamp
    assert precursors[0]["timestamp"] == timeline[0]["timestamp"]
