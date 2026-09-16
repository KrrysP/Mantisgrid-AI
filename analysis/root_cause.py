"""Root-cause investigation scoring engine for MantisGuard."""

from typing import Dict, List, Optional, Tuple, Any
from analysis.schemas import MetricEvent, EvidenceItem, LogEvent, TraceEvent

# Scoring weight constants
WEIGHT_GPU_OVER_90 = 35.0
WEIGHT_QUEUE_GROWTH_OVER_100 = 25.0
WEIGHT_LATENCY_GROWTH_OVER_100 = 25.0
WEIGHT_ERROR_RATE_OVER_5 = 15.0


def score_cluster(
    cluster: str,
    metrics: List[MetricEvent],
    baseline_metrics: Optional[List[MetricEvent]] = None,
) -> Tuple[float, Dict[str, Any], List[EvidenceItem]]:
    """Calculates root cause score, breakdown, and evidence for a specific cluster."""
    cluster_metrics = [m for m in metrics if m.cluster == cluster]
    if not cluster_metrics:
        return 0.0, {}, []

    # Find baseline for this cluster
    baseline = None
    if baseline_metrics:
        for bm in baseline_metrics:
            if bm.cluster == cluster:
                baseline = bm
                break

    # Get worst observed metrics for this cluster
    max_gpu = max(m.gpu_utilization for m in cluster_metrics)
    max_queue = max(m.queue_depth for m in cluster_metrics)
    max_latency = max(m.p95_latency_ms for m in cluster_metrics)
    max_error = max(m.error_rate for m in cluster_metrics)
    latest_event = max(cluster_metrics, key=lambda m: m.timestamp)

    score = 0.0
    breakdown: Dict[str, Any] = {}
    evidence: List[EvidenceItem] = []

    # 1. GPU Utilization > 90%
    if max_gpu >= 90.0:
        score += WEIGHT_GPU_OVER_90
        breakdown["gpu_saturation"] = WEIGHT_GPU_OVER_90
        evidence.append(
            EvidenceItem(
                source_type="metric",
                timestamp=latest_event.timestamp,
                cluster=cluster,
                description=f"GPU utilization reached {max_gpu:.1f}% on {cluster} (exceeded 90% critical threshold)",
                severity="CRITICAL",
                value=max_gpu,
            )
        )

    # 2. Queue growth > 100% vs baseline or queue_depth >= 50
    base_queue = baseline.queue_depth if baseline else 20
    queue_growth = ((max_queue - base_queue) / base_queue) * 100 if base_queue > 0 else 0
    if max_queue >= 50 or queue_growth >= 100.0:
        score += WEIGHT_QUEUE_GROWTH_OVER_100
        breakdown["queue_growth"] = WEIGHT_QUEUE_GROWTH_OVER_100
        evidence.append(
            EvidenceItem(
                source_type="metric",
                timestamp=latest_event.timestamp,
                cluster=cluster,
                description=f"Queue depth reached {max_queue} requests on {cluster} (+{queue_growth:.1f}% growth)",
                severity="CRITICAL" if max_queue >= 70 else "WARN",
                value=float(max_queue),
            )
        )

    # 3. Latency growth > 100% vs baseline or p95_latency >= 1000ms
    base_latency = baseline.p95_latency_ms if baseline else 400.0
    latency_growth = ((max_latency - base_latency) / base_latency) * 100 if base_latency > 0 else 0
    if max_latency >= 1000.0 or latency_growth >= 100.0:
        score += WEIGHT_LATENCY_GROWTH_OVER_100
        breakdown["latency_degradation"] = WEIGHT_LATENCY_GROWTH_OVER_100
        evidence.append(
            EvidenceItem(
                source_type="metric",
                timestamp=latest_event.timestamp,
                cluster=cluster,
                description=f"P95 latency degraded to {max_latency:.1f}ms on {cluster} (+{latency_growth:.1f}% growth)",
                severity="CRITICAL" if max_latency >= 1500.0 else "WARN",
                value=max_latency,
            )
        )

    # 4. Error rate > 5.0%
    if max_error >= 5.0:
        score += WEIGHT_ERROR_RATE_OVER_5
        breakdown["error_rate_spike"] = WEIGHT_ERROR_RATE_OVER_5
        evidence.append(
            EvidenceItem(
                source_type="metric",
                timestamp=latest_event.timestamp,
                cluster=cluster,
                description=f"Error rate elevated to {max_error:.1f}% on {cluster} (exceeded 5.0% warning threshold)",
                severity="CRITICAL" if max_error >= 8.0 else "WARN",
                value=max_error,
            )
        )

    return score, breakdown, evidence


def investigate_root_cause(
    metrics: List[MetricEvent],
    baseline_metrics: Optional[List[MetricEvent]] = None,
    logs: Optional[List[LogEvent]] = None,
    traces: Optional[List[TraceEvent]] = None,
) -> Dict[str, Any]:
    """Investigates root cause by scoring clusters independently and compiling supporting evidence."""
    clusters = sorted(list(set(m.cluster for m in metrics)))

    scores: Dict[str, float] = {}
    breakdowns: Dict[str, Dict[str, Any]] = {}
    all_evidence: List[EvidenceItem] = []

    for cluster in clusters:
        score, breakdown, evidence = score_cluster(cluster, metrics, baseline_metrics)
        scores[cluster] = score
        breakdowns[cluster] = breakdown
        all_evidence.extend(evidence)

    # Incorporate matching error logs/traces into evidence
    if logs:
        for log in logs:
            if log.severity in ("ERROR", "CRITICAL"):
                all_evidence.append(
                    EvidenceItem(
                        source_type="log",
                        timestamp=log.timestamp,
                        cluster=log.cluster,
                        description=f"Log alert ({log.severity}): {log.message}",
                        severity=log.severity,
                        value=None,
                    )
                )

    if traces:
        for trace in traces:
            if trace.status in ("ERROR", "TIMEOUT"):
                all_evidence.append(
                    EvidenceItem(
                        source_type="trace",
                        timestamp=trace.timestamp,
                        cluster=trace.cluster,
                        description=f"Trace span failure ({trace.status}) on {trace.service}: {trace.duration_ms:.1f}ms",
                        severity="ERROR" if trace.status == "TIMEOUT" else "CRITICAL",
                        value=trace.duration_ms,
                    )
                )

    # Sort evidence chronologically
    all_evidence.sort(key=lambda item: item.timestamp)

    # Identify primary affected cluster
    affected_cluster = max(scores, key=scores.get) if scores else "unknown"
    top_score = scores.get(affected_cluster, 0.0)

    # Root cause text
    if top_score >= 50.0:
        root_cause = f"{affected_cluster} overload caused by GPU saturation"
    elif top_score > 0.0:
        root_cause = f"Minor degradation observed on {affected_cluster}"
    else:
        root_cause = "No root cause detected; all clusters operating within nominal bounds"

    # Alternative causes with non-zero scores
    alternative_causes = {
        c: s for c, s in scores.items() if c != affected_cluster and s > 0.0
    }

    return {
        "affected_cluster": affected_cluster,
        "root_cause": root_cause,
        "scores": scores,
        "score_breakdowns": breakdowns,
        "alternative_causes": alternative_causes,
        "evidence": all_evidence,
    }
