"""Confidence score calculator for MantisGuard root-cause investigator."""

from typing import Any, Dict, List, Optional
from analysis.schemas import EvidenceItem, LogEvent, MetricEvent, TraceEvent


def calculate_confidence(
    affected_cluster: str,
    root_cause_result: Dict[str, Any],
    metrics: List[MetricEvent],
    logs: List[LogEvent],
    traces: List[TraceEvent],
    anomalies: List[EvidenceItem],
) -> float:
    """Calculates an evidence-backed confidence score between 0.0 and 100.0."""
    score = 50.0  # Base starting confidence

    # 1. Check multi-telemetry alignment (+20 points)
    sources = set(e.source_type for e in anomalies if e.cluster == affected_cluster)
    has_logs = any(l.cluster == affected_cluster and l.severity in ("WARN", "ERROR", "CRITICAL") for l in logs)
    has_traces = any(t.cluster == affected_cluster and t.status in ("ERROR", "TIMEOUT") for t in traces)

    if "metric" in sources:
        if has_logs and has_traces:
            score += 20.0
        elif has_logs or has_traces:
            score += 10.0

    # 2. Check resource saturation + symptom alignment (+20 points)
    cluster_metrics = [m for m in metrics if m.cluster == affected_cluster]
    if cluster_metrics:
        max_gpu = max(m.gpu_utilization for m in cluster_metrics)
        max_latency = max(m.p95_latency_ms for m in cluster_metrics)
        max_error = max(m.error_rate for m in cluster_metrics)

        # Resource saturation (GPU >= 90%) aligned with symptoms (latency >= 1000ms or error >= 5%)
        if max_gpu >= 90.0 and (max_latency >= 1000.0 or max_error >= 5.0):
            score += 20.0

    # 3. Check stark difference vs healthy cluster (+15 points)
    cluster_scores = root_cause_result.get("scores", {})
    affected_score = cluster_scores.get(affected_cluster, 0.0)
    other_scores = [s for c, s in cluster_scores.items() if c != affected_cluster]

    if other_scores:
        next_highest = max(other_scores)
        if affected_score - next_highest >= 50.0:
            score += 15.0
        elif affected_score - next_highest < 10.0 and affected_score > 0:
            # Score penalty if clusters have ambiguous scores
            score -= 15.0

    # 4. Check chronological ordering (+15 points)
    # Timeline order: GPU saturation -> queue growth -> latency -> error
    if len(anomalies) >= 2:
        gpu_anomalies = [a for a in anomalies if "GPU" in a.description]
        latency_anomalies = [a for a in anomalies if "latency" in a.description or "P95" in a.description]

        if gpu_anomalies and latency_anomalies:
            if gpu_anomalies[0].timestamp <= latency_anomalies[0].timestamp:
                score += 15.0

    # Penalties for missing telemetry
    if not logs:
        score -= 10.0
    if not traces:
        score -= 10.0

    # Clamp confidence between 0.0 and 100.0
    confidence = max(0.0, min(100.0, score))
    return confidence
