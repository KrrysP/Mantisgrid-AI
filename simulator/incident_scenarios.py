"""Incident scenarios definitions for MantisGuard telemetry simulator."""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from analysis.schemas import MetricEvent, LogEvent, TraceEvent

DATA_DIR = Path(__file__).parent.parent / "data"


def load_raw_fixtures() -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
    """Loads raw json fixture dictionaries for baseline metrics, incident metrics, logs, and traces."""
    with open(DATA_DIR / "baseline_metrics.json", "r", encoding="utf-8") as f:
        baseline_metrics = json.load(f)
    with open(DATA_DIR / "incident_metrics.json", "r", encoding="utf-8") as f:
        incident_metrics = json.load(f)
    with open(DATA_DIR / "logs.json", "r", encoding="utf-8") as f:
        logs = json.load(f)
    with open(DATA_DIR / "traces.json", "r", encoding="utf-8") as f:
        traces = json.load(f)
    return baseline_metrics, incident_metrics, logs, traces


def get_healthy_scenario() -> Dict[str, List]:
    """Returns telemetry data for a completely healthy cluster operation scenario."""
    baseline_raw, _, _, _ = load_raw_fixtures()
    metrics = [MetricEvent.model_validate(item) for item in baseline_raw]

    # Simple healthy log & trace entries
    timestamp = metrics[0].timestamp
    logs = [
        LogEvent(
            timestamp=timestamp,
            cluster="cluster-a",
            service="vllm-inference",
            severity="INFO",
            message="Cluster-a inference nodes operating nominally",
        ),
        LogEvent(
            timestamp=timestamp,
            cluster="cluster-b",
            service="vllm-inference",
            severity="INFO",
            message="Cluster-b inference nodes operating nominally",
        ),
    ]
    traces = [
        TraceEvent(
            trace_id="tr-healthy-01",
            timestamp=timestamp,
            cluster="cluster-a",
            service="vllm-inference",
            duration_ms=420.0,
            status="OK",
        ),
        TraceEvent(
            trace_id="tr-healthy-02",
            timestamp=timestamp,
            cluster="cluster-b",
            service="vllm-inference",
            duration_ms=390.0,
            status="OK",
        ),
    ]
    return {
        "baseline_metrics": metrics,
        "metrics": metrics,
        "logs": logs,
        "traces": traces,
    }


def get_cluster_a_overload_scenario() -> Dict[str, List]:
    """Returns telemetry data for the cluster-a overload incident scenario.

    Timeline causal sequence:
    1. GPU saturation (96%) on cluster-a
    2. Request queue growth (76 requests) on cluster-a
    3. Latency increase (1850ms) on cluster-a
    4. Timeout and high error rate (8.4%) logs on cluster-a
    """
    baseline_raw, incident_raw, logs_raw, traces_raw = load_raw_fixtures()
    baseline_metrics = [MetricEvent.model_validate(item) for item in baseline_raw]
    incident_metrics = [MetricEvent.model_validate(item) for item in incident_raw]
    logs = [LogEvent.model_validate(item) for item in logs_raw]
    traces = [TraceEvent.model_validate(item) for item in traces_raw]

    return {
        "baseline_metrics": baseline_metrics,
        "metrics": incident_metrics,
        "logs": logs,
        "traces": traces,
    }
