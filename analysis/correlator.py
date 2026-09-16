"""Event correlation engine for MantisGuard telemetry events."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from analysis.schemas import EvidenceItem, LogEvent, TraceEvent


def correlate_events(
    anomalies: List[EvidenceItem],
    logs: List[LogEvent],
    traces: List[TraceEvent],
    target_cluster: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Correlates metric anomalies, logs, and traces based on cluster, time window, and trace ID."""
    correlated: List[Dict[str, Any]] = []

    # 1. Correlate by trace_id matching
    trace_map: Dict[str, TraceEvent] = {t.trace_id: t for t in traces if t.trace_id}

    for log in logs:
        if target_cluster and log.cluster != target_cluster:
            continue
        if log.severity in ("WARN", "ERROR", "CRITICAL"):
            matched_trace = trace_map.get(log.trace_id) if log.trace_id else None
            entry = {
                "timestamp": log.timestamp.isoformat(),
                "cluster": log.cluster,
                "service": log.service,
                "event_type": "log",
                "severity": log.severity,
                "description": f"Log entry ({log.severity}): {log.message}",
                "trace_id": log.trace_id,
                "matched_trace_status": matched_trace.status if matched_trace else None,
                "correlation_note": f"Log event suggests issue on {log.cluster} in service {log.service}",
            }
            correlated.append(entry)

    for anomaly in anomalies:
        if target_cluster and anomaly.cluster != target_cluster:
            continue
        entry = {
            "timestamp": anomaly.timestamp.isoformat(),
            "cluster": anomaly.cluster,
            "service": "vllm-inference",
            "event_type": "metric_anomaly",
            "severity": anomaly.severity,
            "description": anomaly.description,
            "trace_id": None,
            "matched_trace_status": None,
            "correlation_note": f"Metric anomaly supports potential performance degradation on {anomaly.cluster}",
        }
        correlated.append(entry)

    # Sort chronologically
    correlated.sort(key=lambda x: x["timestamp"])
    return correlated


def build_timeline(
    anomalies: List[EvidenceItem],
    logs: List[LogEvent],
    traces: List[TraceEvent],
) -> List[Dict[str, Any]]:
    """Builds a unified chronological timeline of all anomalous metrics, logs, and traces."""
    timeline = correlate_events(anomalies, logs, traces)
    for idx, item in enumerate(timeline):
        item["sequence_index"] = idx + 1
    return timeline


def identify_precursor_events(timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identifies earliest precursor events in the chronological timeline.

    Returns the initial root symptom events that preceded secondary errors.
    """
    if not timeline:
        return []

    # Sort timeline chronologically
    sorted_timeline = sorted(timeline, key=lambda x: x["timestamp"])
    first_event = sorted_timeline[0]

    precursors = [first_event]
    # Add any events occurring within 30 seconds of first event as co-precursors
    first_dt = datetime.fromisoformat(first_event["timestamp"])
    for item in sorted_timeline[1:]:
        item_dt = datetime.fromisoformat(item["timestamp"])
        if (item_dt - first_dt).total_seconds() <= 30.0:
            precursors.append(item)

    return precursors
