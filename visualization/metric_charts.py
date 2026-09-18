"""Chart adapters that format InvestigationResult timeline and cluster health data."""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go


TIMELINE_COLUMNS = [
    "sequence_index",
    "timestamp",
    "cluster",
    "service",
    "event_type",
    "severity",
    "description",
    "trace_id",
]

SEVERITY_COLORS = {
    "INFO": "#28a745",
    "WARN": "#fd7e14",
    "ERROR": "#dc3545",
    "CRITICAL": "#9b1b30",
}

HEALTH_COLORS = {
    "HEALTHY": "#28a745",
    "DEGRADED": "#fd7e14",
    "CRITICAL": "#dc3545",
}


def timeline_to_dataframe(correlated_timeline: Optional[List[Dict[str, Any]]]) -> pd.DataFrame:
    """Safely converts InvestigationResult.correlated_timeline into a DataFrame."""
    empty = pd.DataFrame(columns=TIMELINE_COLUMNS)
    if not correlated_timeline:
        return empty

    rows = []
    for event in correlated_timeline:
        if not isinstance(event, dict):
            continue
        timestamp = event.get("timestamp")
        parsed_ts = pd.to_datetime(timestamp, errors="coerce", utc=True)
        rows.append(
            {
                "sequence_index": event.get("sequence_index"),
                "timestamp": parsed_ts,
                "cluster": event.get("cluster", ""),
                "service": event.get("service", ""),
                "event_type": event.get("event_type", ""),
                "severity": event.get("severity", ""),
                "description": event.get("description", ""),
                "trace_id": event.get("trace_id") or "",
            }
        )

    if not rows:
        return empty

    df = pd.DataFrame(rows, columns=TIMELINE_COLUMNS)
    if df["timestamp"].notna().any():
        df = df.sort_values("timestamp", kind="stable")
    return df.reset_index(drop=True)


def cluster_health_to_dataframe(cluster_health: Optional[List[Dict[str, Any]]]) -> pd.DataFrame:
    """Safely converts InvestigationResult.cluster_health into a comparison DataFrame."""
    columns = [
        "cluster",
        "gpu_utilization",
        "queue_depth",
        "p95_latency_ms",
        "error_rate",
        "root_cause_score",
        "health_status",
    ]
    empty = pd.DataFrame(columns=columns)
    if not cluster_health:
        return empty

    rows = []
    for item in cluster_health:
        if not isinstance(item, dict):
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            else:
                continue
        rows.append(
            {
                "cluster": item.get("cluster", "unknown"),
                "gpu_utilization": item.get("gpu_utilization", 0.0),
                "queue_depth": item.get("queue_depth", 0),
                "p95_latency_ms": item.get("p95_latency_ms", 0.0),
                "error_rate": item.get("error_rate", 0.0),
                "root_cause_score": item.get("root_cause_score", 0.0),
                "health_status": item.get("health_status", "HEALTHY"),
            }
        )

    return pd.DataFrame(rows, columns=columns) if rows else empty


def create_cluster_metric_chart(
    df: pd.DataFrame,
    metric_col: str,
    title: str,
    unit: str,
) -> go.Figure:
    """Creates a cluster comparison bar chart from real cluster_health values."""
    fig = go.Figure()
    if df is None or df.empty or metric_col not in df.columns:
        fig.update_layout(
            title=dict(text=f"{title} (no data)", font=dict(size=14)),
            height=260,
            template="plotly_white",
        )
        return fig

    colors = [
        HEALTH_COLORS.get(str(status).upper(), "#636EFA")
        for status in df["health_status"].tolist()
    ]
    fig.add_trace(
        go.Bar(
            x=df["cluster"],
            y=df[metric_col],
            marker_color=colors,
            text=[_format_chart_value(v, unit) for v in df[metric_col]],
            textposition="auto",
            hovertemplate="%{x}<br>%{y}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        height=260,
        yaxis=dict(title=unit),
        xaxis=dict(title="Cluster"),
        template="plotly_white",
        showlegend=False,
    )
    return fig


def create_event_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a scatter timeline from correlated telemetry events."""
    fig = go.Figure()
    if df is None or df.empty or df["timestamp"].isna().all():
        fig.update_layout(
            title=dict(text="Correlated Event Timeline (no events)", font=dict(size=14)),
            height=280,
            template="plotly_white",
        )
        return fig

    for severity, color in SEVERITY_COLORS.items():
        subset = df[df["severity"] == severity]
        if subset.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=subset["timestamp"],
                y=subset["cluster"],
                mode="markers+text",
                name=severity,
                marker=dict(size=12, color=color),
                text=subset["sequence_index"].astype(str),
                textposition="top center",
                customdata=subset[["severity", "event_type", "description", "trace_id"]],
                hovertemplate=(
                    "%{x}<br>%{y}<br>"
                    "Severity: %{customdata[0]}<br>"
                    "Type: %{customdata[1]}<br>"
                    "%{customdata[2]}<br>"
                    "Trace: %{customdata[3]}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=dict(text="Correlated Event Timeline", font=dict(size=14)),
        margin=dict(l=20, r=20, t=40, b=20),
        height=280,
        yaxis=dict(title="Cluster"),
        xaxis=dict(title="Time"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
    )
    return fig


def _format_chart_value(value: Any, unit: str) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if "ms" in unit.lower():
        return f"{numeric:.1f}"
    if "%" in unit:
        return f"{numeric:.1f}"
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.1f}"
