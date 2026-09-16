"""Unit tests for telemetry anomaly detection functions."""

from datetime import datetime
from analysis.schemas import MetricEvent
from analysis.detector import (
    detect_gpu_anomaly,
    detect_queue_anomaly,
    detect_latency_anomaly,
    detect_error_rate_anomaly,
    detect_all_anomalies,
)
from simulator.telemetry_generator import get_all_telemetry


def test_gpu_anomaly_detection():
    event = MetricEvent(
        timestamp=datetime.now(),
        cluster="cluster-a",
        service="vllm-inference",
        gpu_utilization=96.0,
        gpu_memory_utilization=94.0,
        queue_depth=20,
        p95_latency_ms=400.0,
        error_rate=0.5,
        request_rate=100.0,
    )
    anomalies = detect_gpu_anomaly([event])
    assert len(anomalies) == 1
    assert anomalies[0].cluster == "cluster-a"
    assert anomalies[0].severity == "CRITICAL"
    assert anomalies[0].value == 96.0


def test_queue_anomaly_detection():
    event = MetricEvent(
        timestamp=datetime.now(),
        cluster="cluster-a",
        service="vllm-inference",
        gpu_utilization=60.0,
        gpu_memory_utilization=50.0,
        queue_depth=76,
        p95_latency_ms=400.0,
        error_rate=0.5,
        request_rate=100.0,
    )
    anomalies = detect_queue_anomaly([event])
    assert len(anomalies) == 1
    assert anomalies[0].cluster == "cluster-a"
    assert anomalies[0].value == 76.0


def test_latency_anomaly_detection():
    event = MetricEvent(
        timestamp=datetime.now(),
        cluster="cluster-a",
        service="vllm-inference",
        gpu_utilization=60.0,
        gpu_memory_utilization=50.0,
        queue_depth=20,
        p95_latency_ms=1850.0,
        error_rate=0.5,
        request_rate=100.0,
    )
    anomalies = detect_latency_anomaly([event])
    assert len(anomalies) == 1
    assert anomalies[0].cluster == "cluster-a"
    assert anomalies[0].severity == "CRITICAL"
    assert anomalies[0].value == 1850.0


def test_error_rate_anomaly_detection():
    event = MetricEvent(
        timestamp=datetime.now(),
        cluster="cluster-a",
        service="vllm-inference",
        gpu_utilization=60.0,
        gpu_memory_utilization=50.0,
        queue_depth=20,
        p95_latency_ms=400.0,
        error_rate=8.4,
        request_rate=100.0,
    )
    anomalies = detect_error_rate_anomaly([event])
    assert len(anomalies) == 1
    assert anomalies[0].cluster == "cluster-a"
    assert anomalies[0].severity == "CRITICAL"
    assert anomalies[0].value == 8.4


def test_healthy_data_produces_no_critical_anomalies():
    baseline, metrics, _, _ = get_all_telemetry("healthy")
    anomalies = detect_all_anomalies(metrics, baseline)
    assert len(anomalies) == 0


def test_cluster_a_overload_produces_anomalies():
    baseline, metrics, _, _ = get_all_telemetry("cluster_a_overload")
    anomalies = detect_all_anomalies(metrics, baseline)
    assert len(anomalies) > 0
    cluster_a_anomalies = [a for a in anomalies if a.cluster == "cluster-a"]
    assert len(cluster_a_anomalies) >= 4
