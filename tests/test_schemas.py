"""Unit tests for Pydantic telemetry data models."""

from datetime import datetime
import pytest
from pydantic import ValidationError
from analysis.schemas import (
    MetricEvent,
    LogEvent,
    TraceEvent,
    EvidenceItem,
    ClusterHealth,
    Recommendation,
    InvestigationResult,
)


def test_valid_metric_event_creation():
    event = MetricEvent(
        timestamp=datetime.now(),
        cluster="cluster-a",
        service="vllm-inference",
        gpu_utilization=96.0,
        gpu_memory_utilization=94.0,
        queue_depth=76,
        p95_latency_ms=1850.0,
        error_rate=8.4,
        request_rate=125.0,
    )
    assert event.cluster == "cluster-a"
    assert event.gpu_utilization == 96.0
    assert event.queue_depth == 76


def test_invalid_negative_latency():
    with pytest.raises(ValidationError):
        MetricEvent(
            timestamp=datetime.now(),
            cluster="cluster-a",
            service="vllm-inference",
            gpu_utilization=50.0,
            gpu_memory_utilization=50.0,
            queue_depth=10,
            p95_latency_ms=-10.0,  # invalid negative latency
            error_rate=1.0,
            request_rate=100.0,
        )


def test_invalid_error_rate_out_of_bounds():
    with pytest.raises(ValidationError):
        MetricEvent(
            timestamp=datetime.now(),
            cluster="cluster-a",
            service="vllm-inference",
            gpu_utilization=50.0,
            gpu_memory_utilization=50.0,
            queue_depth=10,
            p95_latency_ms=100.0,
            error_rate=150.0,  # invalid error rate > 100%
            request_rate=100.0,
        )


def test_valid_log_event_creation():
    log = LogEvent(
        timestamp=datetime.now(),
        cluster="cluster-a",
        service="vllm-inference",
        severity="ERROR",
        message="P95 inference latency severe degradation",
        trace_id="tr-003",
    )
    assert log.severity == "ERROR"
    assert log.trace_id == "tr-003"


def test_valid_trace_event_creation():
    trace = TraceEvent(
        trace_id="tr-001",
        timestamp=datetime.now(),
        cluster="cluster-a",
        service="vllm-inference",
        duration_ms=1850.0,
        status="TIMEOUT",
    )
    assert trace.status == "TIMEOUT"
    assert trace.duration_ms == 1850.0
