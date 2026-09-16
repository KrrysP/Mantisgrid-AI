"""Anomaly detection algorithms for MantisGuard telemetry metrics."""

from typing import Dict, List, Optional
from analysis.schemas import MetricEvent, EvidenceItem

# Configured threshold values
GPU_UTILIZATION_WARN = 85.0
GPU_UTILIZATION_CRITICAL = 90.0
QUEUE_DEPTH_WARN = 50
P95_LATENCY_WARN_MS = 1000.0
ERROR_RATE_WARN = 5.0


def _find_baseline(
    cluster: str, baseline_metrics: Optional[List[MetricEvent]]
) -> Optional[MetricEvent]:
    """Helper to find baseline metric event for a given cluster."""
    if not baseline_metrics:
        return None
    for item in baseline_metrics:
        if item.cluster == cluster:
            return item
    return None


def detect_gpu_anomaly(
    metrics: List[MetricEvent],
    baseline_metrics: Optional[List[MetricEvent]] = None,
) -> List[EvidenceItem]:
    """Detects GPU utilization anomalies using static thresholds and baseline comparisons."""
    anomalies: List[EvidenceItem] = []
    for event in metrics:
        baseline = _find_baseline(event.cluster, baseline_metrics)
        base_gpu = baseline.gpu_utilization if baseline else None

        if event.gpu_utilization >= GPU_UTILIZATION_WARN:
            severity = "CRITICAL" if event.gpu_utilization >= GPU_UTILIZATION_CRITICAL else "WARN"
            pct_change_str = ""
            if base_gpu and base_gpu > 0:
                pct_change = ((event.gpu_utilization - base_gpu) / base_gpu) * 100
                pct_change_str = f" (+{pct_change:.1f}% vs baseline {base_gpu:.1f}%)"

            desc = (
                f"GPU utilization metric spike on {event.cluster}: "
                f"current {event.gpu_utilization:.1f}% exceeds threshold {GPU_UTILIZATION_WARN:.1f}%{pct_change_str}"
            )
            anomalies.append(
                EvidenceItem(
                    source_type="metric",
                    timestamp=event.timestamp,
                    cluster=event.cluster,
                    description=desc,
                    severity=severity,
                    value=event.gpu_utilization,
                )
            )
    return anomalies


def detect_queue_anomaly(
    metrics: List[MetricEvent],
    baseline_metrics: Optional[List[MetricEvent]] = None,
) -> List[EvidenceItem]:
    """Detects request queue depth anomalies."""
    anomalies: List[EvidenceItem] = []
    for event in metrics:
        baseline = _find_baseline(event.cluster, baseline_metrics)
        base_queue = baseline.queue_depth if baseline else None

        if event.queue_depth >= QUEUE_DEPTH_WARN:
            pct_change_str = ""
            if base_queue is not None and base_queue > 0:
                pct_change = ((event.queue_depth - base_queue) / base_queue) * 100
                pct_change_str = f" (+{pct_change:.1f}% vs baseline {base_queue})"

            desc = (
                f"Queue depth metric growth on {event.cluster}: "
                f"current {event.queue_depth} requests exceeds threshold {QUEUE_DEPTH_WARN}{pct_change_str}"
            )
            anomalies.append(
                EvidenceItem(
                    source_type="metric",
                    timestamp=event.timestamp,
                    cluster=event.cluster,
                    description=desc,
                    severity="WARN" if event.queue_depth < 70 else "CRITICAL",
                    value=float(event.queue_depth),
                )
            )
    return anomalies


def detect_latency_anomaly(
    metrics: List[MetricEvent],
    baseline_metrics: Optional[List[MetricEvent]] = None,
) -> List[EvidenceItem]:
    """Detects P95 latency anomalies."""
    anomalies: List[EvidenceItem] = []
    for event in metrics:
        baseline = _find_baseline(event.cluster, baseline_metrics)
        base_lat = baseline.p95_latency_ms if baseline else None

        if event.p95_latency_ms >= P95_LATENCY_WARN_MS:
            pct_change_str = ""
            if base_lat and base_lat > 0:
                pct_change = ((event.p95_latency_ms - base_lat) / base_lat) * 100
                pct_change_str = f" (+{pct_change:.1f}% vs baseline {base_lat:.1f}ms)"

            desc = (
                f"P95 latency metric degradation on {event.cluster}: "
                f"current {event.p95_latency_ms:.1f}ms exceeds threshold {P95_LATENCY_WARN_MS:.1f}ms{pct_change_str}"
            )
            anomalies.append(
                EvidenceItem(
                    source_type="metric",
                    timestamp=event.timestamp,
                    cluster=event.cluster,
                    description=desc,
                    severity="CRITICAL" if event.p95_latency_ms >= 1500.0 else "WARN",
                    value=event.p95_latency_ms,
                )
            )
    return anomalies


def detect_error_rate_anomaly(
    metrics: List[MetricEvent],
    baseline_metrics: Optional[List[MetricEvent]] = None,
) -> List[EvidenceItem]:
    """Detects error rate anomalies."""
    anomalies: List[EvidenceItem] = []
    for event in metrics:
        baseline = _find_baseline(event.cluster, baseline_metrics)
        base_err = baseline.error_rate if baseline else None

        if event.error_rate >= ERROR_RATE_WARN:
            pct_change_str = ""
            if base_err and base_err > 0:
                pct_change = ((event.error_rate - base_err) / base_err) * 100
                pct_change_str = f" (+{pct_change:.1f}% vs baseline {base_err:.1f}%)"

            desc = (
                f"Error rate metric spike on {event.cluster}: "
                f"current {event.error_rate:.1f}% exceeds threshold {ERROR_RATE_WARN:.1f}%{pct_change_str}"
            )
            anomalies.append(
                EvidenceItem(
                    source_type="metric",
                    timestamp=event.timestamp,
                    cluster=event.cluster,
                    description=desc,
                    severity="CRITICAL" if event.error_rate >= 8.0 else "WARN",
                    value=event.error_rate,
                )
            )
    return anomalies


def detect_all_anomalies(
    metrics: List[MetricEvent],
    baseline_metrics: Optional[List[MetricEvent]] = None,
) -> List[EvidenceItem]:
    """Detects all metric anomalies across GPU utilization, queue depth, latency, and error rate."""
    all_anomalies: List[EvidenceItem] = []
    all_anomalies.extend(detect_gpu_anomaly(metrics, baseline_metrics))
    all_anomalies.extend(detect_queue_anomaly(metrics, baseline_metrics))
    all_anomalies.extend(detect_latency_anomaly(metrics, baseline_metrics))
    all_anomalies.extend(detect_error_rate_anomaly(metrics, baseline_metrics))

    # Sort anomalies chronologically
    all_anomalies.sort(key=lambda item: item.timestamp)
    return all_anomalies
