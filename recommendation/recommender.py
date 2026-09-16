"""Recommendation engine and cluster health assessment for MantisGuard."""

from typing import Dict, List, Optional
from analysis.schemas import ClusterHealth, MetricEvent, Recommendation


def calculate_cluster_health(
    metrics: List[MetricEvent],
    root_cause_scores: Optional[Dict[str, float]] = None,
) -> List[ClusterHealth]:
    """Calculates operational health status for all monitored clusters based on latest telemetry."""
    if not root_cause_scores:
        root_cause_scores = {}

    clusters = sorted(list(set(m.cluster for m in metrics)))
    health_list: List[ClusterHealth] = []

    for cluster in clusters:
        cluster_metrics = [m for m in metrics if m.cluster == cluster]
        if not cluster_metrics:
            continue

        # Get worst metrics observed for cluster
        max_gpu = max(m.gpu_utilization for m in cluster_metrics)
        max_queue = max(m.queue_depth for m in cluster_metrics)
        max_latency = max(m.p95_latency_ms for m in cluster_metrics)
        max_error = max(m.error_rate for m in cluster_metrics)
        score = root_cause_scores.get(cluster, 0.0)

        # Health status determination
        if max_error >= 5.0 or score >= 50.0 or max_gpu >= 90.0:
            status = "CRITICAL"
        elif max_gpu >= 85.0 or max_queue >= 50 or max_latency >= 1000.0 or score > 0:
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        health_list.append(
            ClusterHealth(
                cluster=cluster,
                gpu_utilization=max_gpu,
                queue_depth=max_queue,
                p95_latency_ms=max_latency,
                error_rate=max_error,
                root_cause_score=score,
                health_status=status,
            )
        )

    return health_list


def select_healthiest_cluster(
    health_list: List[ClusterHealth],
    exclude_cluster: Optional[str] = None,
) -> Optional[str]:
    """Selects the healthiest target cluster sorted by lowest error rate, latency, GPU, and queue depth."""
    candidates = [ch for ch in health_list if ch.cluster != exclude_cluster]
    if not candidates:
        return None

    # Sorting key priority:
    # 1. Lower error rate
    # 2. Lower P95 latency
    # 3. Lower GPU utilization
    # 4. Lower queue depth
    candidates.sort(
        key=lambda ch: (
            ch.error_rate,
            ch.p95_latency_ms,
            ch.gpu_utilization,
            ch.queue_depth,
        )
    )

    return candidates[0].cluster


def generate_recommendation(
    affected_cluster: str,
    root_cause: str,
    health_list: List[ClusterHealth],
) -> Recommendation:
    """Generates an actionable traffic remediation recommendation."""
    target_cluster = select_healthiest_cluster(health_list, exclude_cluster=affected_cluster)

    if target_cluster:
        reason = (
            f"{target_cluster} has lower latency, fewer errors, and available capacity "
            f"to absorb workload from overloaded {affected_cluster}."
        )
        return Recommendation(
            action="shift traffic",
            source_cluster=affected_cluster,
            target_cluster=target_cluster,
            traffic_percentage=30.0,
            reason=reason,
            safety_notes="Simulated recommendation only. Verify target cluster capacity before execution.",
        )
    else:
        return Recommendation(
            action="scale cluster",
            source_cluster=affected_cluster,
            target_cluster=None,
            traffic_percentage=0.0,
            reason=f"No healthy target clusters available to receive traffic from {affected_cluster}.",
            safety_notes="Simulated recommendation only. Add capacity or apply rate limiting.",
        )
