import streamlit as st

from pipeline.investigator import run_investigation
from visualization.dashboard_components import (
    format_ms,
    format_pct,
    format_queue,
    health_color,
    lookup_cluster_health,
    pretty_cluster,
    render_header,
    render_metric_card,
)
from visualization.metric_charts import (
    cluster_health_to_dataframe,
    create_cluster_metric_chart,
    create_event_timeline_chart,
    timeline_to_dataframe,
)

st.set_page_config(
    page_title="MantisGuard - AI Infrastructure Reliability Investigator",
    page_icon="🛡️",
    layout="wide",
)


def load_investigation(scenario_name: str) -> None:
    """Runs the investigation pipeline and stores the result in session state."""
    try:
        st.session_state.investigation_result = run_investigation(scenario_name)
        st.session_state.investigation_error = None
        st.session_state.scenario_name = scenario_name
        st.session_state.recommendation_applied = False
    except Exception as exc:
        st.session_state.investigation_error = str(exc)


def apply_recommendation() -> None:
    st.session_state.recommendation_applied = True


# -------------------------------------------------------------------
# State Management
# -------------------------------------------------------------------
if "recommendation_applied" not in st.session_state:
    st.session_state.recommendation_applied = False

if "investigation_error" not in st.session_state:
    st.session_state.investigation_error = None

if "scenario_name" not in st.session_state:
    st.session_state.scenario_name = "healthy"

if "investigation_result" not in st.session_state:
    load_investigation("healthy")

# -------------------------------------------------------------------
# Error handling
# -------------------------------------------------------------------
if st.session_state.investigation_error:
    st.error(f"Investigation Engine Failed: {st.session_state.investigation_error}")
    st.info("The dashboard could not load investigation results. Try returning to the healthy baseline.")
    if st.button("🔄 Return to Healthy"):
        load_investigation("healthy")
        st.rerun()
    st.stop()

result = st.session_state.investigation_result
if result is None:
    st.error("Investigation Engine Failed: no investigation result is available.")
    st.stop()

payload = result.model_dump()
cluster_health = payload.get("cluster_health") or []
timeline_events = payload.get("correlated_timeline") or []
evidence_items = payload.get("evidence") or []
recommendation = payload.get("recommendation") or {}

cluster_a = lookup_cluster_health(cluster_health, "cluster-a")
cluster_b = lookup_cluster_health(cluster_health, "cluster-b")
color_a = health_color(cluster_a.get("health_status"))
color_b = health_color(cluster_b.get("health_status"))
incident = result.severity in ("WARN", "ERROR", "CRITICAL")
display_status = result.severity if incident else "HEALTHY"
display_affected = result.affected_cluster if incident else "None"
display_confidence = f"{result.confidence:.1f}%" if incident else "N/A"

# -------------------------------------------------------------------
# 1. Header & Controls
# -------------------------------------------------------------------
render_header(display_status)

st.divider()

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
with col_btn1:
    if st.button(
        "🚨 Simulate Incident",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.scenario_name == "cluster_a_overload",
    ):
        load_investigation("cluster_a_overload")
        st.rerun()

with col_btn2:
    if st.button(
        "🔄 Return to Healthy",
        use_container_width=True,
        disabled=st.session_state.scenario_name == "healthy",
    ):
        load_investigation("healthy")
        st.rerun()

# -------------------------------------------------------------------
# 2. Incident Banner
# -------------------------------------------------------------------
if not incident:
    st.success("No active incidents detected. All clusters are operating within normal thresholds.")
elif result.severity in ("ERROR", "CRITICAL"):
    st.error(f"🚨 **{result.incident_title}**")
elif result.severity == "WARN":
    st.warning(f"⚠️ **{result.incident_title}**")

# -------------------------------------------------------------------
# 3. KPI row
# -------------------------------------------------------------------
k1, k2, k3 = st.columns(3)
k1.metric("Affected Cluster", display_affected)
k2.metric("Severity", display_status)
k3.metric("Confidence", display_confidence)

# -------------------------------------------------------------------
# 4. Side-by-Side Status & Metric Cards
# -------------------------------------------------------------------
st.subheader("Cluster Overview")

h1, h2 = st.columns(2)
with h1:
    st.metric("Cluster A Health", cluster_a.get("health_status", "HEALTHY"))
with h2:
    st.metric("Cluster B Health", cluster_b.get("health_status", "HEALTHY"))

m1, m2, m3, m4 = st.columns(4)

with m1:
    render_metric_card(
        "Inference Latency",
        format_ms(cluster_a.get("p95_latency_ms", 0.0)),
        format_ms(cluster_b.get("p95_latency_ms", 0.0)),
        status_a=color_a,
        status_b=color_b,
    )

with m2:
    render_metric_card(
        "Error Rate",
        format_pct(cluster_a.get("error_rate", 0.0)),
        format_pct(cluster_b.get("error_rate", 0.0)),
        status_a=color_a,
        status_b=color_b,
    )

with m3:
    render_metric_card(
        "GPU Utilization",
        format_pct(cluster_a.get("gpu_utilization", 0.0)),
        format_pct(cluster_b.get("gpu_utilization", 0.0)),
        status_a=color_a,
        status_b=color_b,
    )

with m4:
    render_metric_card(
        "Queue Depth",
        format_queue(cluster_a.get("queue_depth", 0)),
        format_queue(cluster_b.get("queue_depth", 0)),
        status_a=color_a,
        status_b=color_b,
    )

st.divider()

# -------------------------------------------------------------------
# 5. Charts from real investigation data
# -------------------------------------------------------------------
st.subheader("Cluster Health Comparison")
health_df = cluster_health_to_dataframe(cluster_health)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        create_cluster_metric_chart(health_df, "gpu_utilization", "GPU Utilization", "Utilization (%)"),
        use_container_width=True,
    )
    st.plotly_chart(
        create_cluster_metric_chart(health_df, "p95_latency_ms", "Inference Latency", "Latency (ms)"),
        use_container_width=True,
    )

with c2:
    st.plotly_chart(
        create_cluster_metric_chart(health_df, "queue_depth", "Queue Depth", "Requests in Queue"),
        use_container_width=True,
    )
    st.plotly_chart(
        create_cluster_metric_chart(health_df, "error_rate", "Error Rate", "Error Rate (%)"),
        use_container_width=True,
    )

st.subheader("Unified Telemetry Timeline")
timeline_df = timeline_to_dataframe(timeline_events)
if timeline_df.empty:
    st.info("No anomalous timeline events in the current investigation.")
else:
    st.plotly_chart(create_event_timeline_chart(timeline_df), use_container_width=True)
    for event in timeline_events:
        st.markdown(
            f"**Step {event.get('sequence_index', '')}** | `{event.get('timestamp', '')}` | "
            f"**{event.get('cluster', '')}** | `{event.get('severity', '')}` | "
            f"{event.get('description', '')}"
        )

st.divider()

# -------------------------------------------------------------------
# 6. Evidence & Investigation
# -------------------------------------------------------------------
st.subheader("Investigation Findings")

metric_evidence = [item for item in evidence_items if item.get("source_type") == "metric"]
log_evidence = [item for item in evidence_items if item.get("source_type") == "log"]
trace_evidence = [item for item in evidence_items if item.get("source_type") == "trace"]

e1, e2, e3 = st.columns(3)

with e1:
    st.markdown("### 📊 Metrics Evidence")
    if metric_evidence:
        for item in metric_evidence:
            st.write(f"• **{item.get('cluster', '')}:** {item.get('description', '')}")
    else:
        st.info("Metrics are within normal baseline levels.")

with e2:
    st.markdown("### 📜 Logs Evidence")
    if log_evidence:
        for item in log_evidence:
            st.write(f"• **{item.get('severity', '')}:** {item.get('description', '')}")
    else:
        st.info("No anomalous log events detected.")

with e3:
    st.markdown("### 🔍 Traces Evidence")
    if trace_evidence:
        for item in trace_evidence:
            st.write(f"• **{item.get('cluster', '')}:** {item.get('description', '')}")
    else:
        st.info("No failed or timeout traces detected.")

st.divider()

# -------------------------------------------------------------------
# 7. Root Cause & Recommendations
# -------------------------------------------------------------------
r_col1, r_col2 = st.columns(2)

with r_col1:
    st.markdown("### 🎯 Root Cause Analysis")
    if incident:
        st.error(f"**Root Cause:** {result.root_cause}")
        st.metric(label="Confidence Score", value=f"{result.confidence:.1f}%")
    else:
        st.success("**Root Cause:** No active incidents identified.")

with r_col2:
    st.markdown("### 💡 Recommended Action")
    action = str(recommendation.get("action", "")).strip()
    source_cluster = recommendation.get("source_cluster")
    target_cluster = recommendation.get("target_cluster")
    traffic_percentage = recommendation.get("traffic_percentage")
    reason = recommendation.get("reason", "")
    safety_notes = recommendation.get("safety_notes", "")

    if incident:
        st.warning(f"**Action:** {action}")
        st.write(f"**Source:** {source_cluster}")
        st.write(f"**Target:** {target_cluster or 'n/a'}")
        if traffic_percentage is not None:
            st.write(f"**Traffic Shift:** {traffic_percentage:.1f}%")
        st.write(f"**Reason:** {reason}")
        st.caption(safety_notes)

        if not st.session_state.recommendation_applied:
            st.button(
                "Apply Recommendation",
                on_click=apply_recommendation,
                type="primary",
            )
        else:
            action_lower = action.lower()
            if "shift" in action_lower and target_cluster:
                st.success(
                    "Recommendation applied successfully. "
                    f"Traffic is being shifted from {pretty_cluster(source_cluster)} "
                    f"to {pretty_cluster(target_cluster)}."
                )
            else:
                st.success(
                    f"Recommendation applied successfully. {action}: {reason}"
                )
    else:
        st.info("System healthy. No remediation needed.")

st.divider()

# -------------------------------------------------------------------
# 8. AI Executive Summary
# -------------------------------------------------------------------
st.subheader("🤖 AI Incident Report")
if incident:
    st.markdown(f"> {result.explanation}")
else:
    st.markdown(
        "> All clusters are operating within operational thresholds. "
        "No resource bottlenecks or traffic routing anomalies observed."
    )
