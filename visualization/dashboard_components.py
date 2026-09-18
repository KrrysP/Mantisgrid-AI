import streamlit as st


def pretty_cluster(name: str) -> str:
    """Formats cluster-a style identifiers as 'Cluster A'."""
    if not name:
        return "Unknown"
    parts = str(name).replace("_", "-").split("-")
    if len(parts) == 2 and parts[0].lower() == "cluster":
        return f"Cluster {parts[1].upper()}"
    return str(name)


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def format_ms(value: float) -> str:
    return f"{value:.1f} ms"


def format_queue(value: float) -> str:
    return f"{int(value)}"


def health_color(health_status: str) -> str:
    """Maps cluster health_status to metric card color keys."""
    status = (health_status or "HEALTHY").upper()
    if status == "CRITICAL":
        return "red"
    if status == "DEGRADED":
        return "orange"
    return "green"


def lookup_cluster_health(cluster_health: list, cluster_id: str) -> dict:
    """Returns a cluster health dict by cluster name, or empty defaults."""
    for item in cluster_health or []:
        if isinstance(item, dict):
            name = item.get("cluster")
            if name == cluster_id:
                return item
        elif getattr(item, "cluster", None) == cluster_id:
            return item.model_dump() if hasattr(item, "model_dump") else dict(item)
    return {
        "cluster": cluster_id,
        "gpu_utilization": 0.0,
        "queue_depth": 0,
        "p95_latency_ms": 0.0,
        "error_rate": 0.0,
        "root_cause_score": 0.0,
        "health_status": "HEALTHY",
    }


def render_header(severity: str):
    """Renders the dashboard top header with status badge from investigation severity."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("MantisGuard")
        st.caption("AI Infrastructure Reliability Investigator")

    with col2:
        st.write("##")
        level = (severity or "INFO").upper()
        if level in ("INFO", "HEALTHY"):
            st.success("System Status: HEALTHY")
        elif level in ("WARN", "DEGRADED"):
            st.warning("System Status: DEGRADED")
        else:
            st.error(f"System Status: {level}")


def render_metric_card(
    label: str,
    val_a: str,
    val_b: str,
    status_a: str = "green",
    status_b: str = "green",
):
    """Renders a custom dual-cluster comparative metric card."""
    color_map = {"green": "#28a745", "orange": "#fd7e14", "red": "#dc3545"}

    st.markdown(
        f"""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 12px; background-color: #f8f9fa;">
            <div style="font-weight: 600; font-size: 14px; color: #555; margin-bottom: 8px;">{label}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 12px; color: #777;">Cluster A:</span>
                    <span style="font-weight: bold; font-size: 16px; color: {color_map.get(status_a, '#000')}; margin-left: 4px;">{val_a}</span>
                </div>
                <div>
                    <span style="font-size: 12px; color: #777;">Cluster B:</span>
                    <span style="font-weight: bold; font-size: 16px; color: {color_map.get(status_b, '#000')}; margin-left: 4px;">{val_b}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
