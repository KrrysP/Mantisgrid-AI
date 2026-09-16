import streamlit as st
from visualization.dashboard_components import render_header, render_metric_card
from visualization.metric_charts import (
    create_timeline_chart,
    generate_timeline_data,
)

st.set_page_config(
    page_title="MantisGuard - AI Infrastructure Reliability Investigator",
    page_icon="🛡️",
    layout="wide",
)

# -------------------------------------------------------------------
# State Management
# -------------------------------------------------------------------
if "incident_active" not in st.session_state:
    st.session_state.incident_active = False

if "recommendation_applied" not in st.session_state:
    st.session_state.recommendation_applied = False


def trigger_incident():
    st.session_state.incident_active = True
    st.session_state.recommendation_applied = False


def apply_recommendation():
    st.session_state.recommendation_applied = True


# -------------------------------------------------------------------
# Data Setup based on State
# -------------------------------------------------------------------
incident = st.session_state.incident_active

status = "Critical" if incident else "Healthy"
cluster_a_status = "Critical" if incident else "Healthy"
cluster_b_status = "Healthy"

# Metrics
cluster_a_metrics = {
    "latency": "500 ms" if incident else "200 ms",
    "error_rate": "15%" if incident else "1%",
    "gpu_util": "96%" if incident else "60%",
    "queue_depth": "180" if incident else "20",
}

cluster_b_metrics = {
    "latency": "190 ms",
    "error_rate": "0.5%",
    "gpu_util": "58%",
    "queue_depth": "25",
}

# Metric Status Colors (green, orange, red)
color_a = "red" if incident else "green"
color_b = "green"

# -------------------------------------------------------------------
# 1. Header & Controls
# -------------------------------------------------------------------
render_header(status)

st.divider()

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if not incident:
        st.button(
            "🚨 Simulate Incident",
            on_click=trigger_incident,
            type="primary",
            use_container_width=True,
        )
    else:
        st.button(
            "🔄 Reset Dashboard",
            on_click=lambda: st.session_state.update(
                incident_active=False, recommendation_applied=False
            ),
            use_container_width=True,
        )

# -------------------------------------------------------------------
# 2. Incident Banner
# -------------------------------------------------------------------
if incident:
    st.error("🚨 **Critical incident detected in Cluster A**")

# -------------------------------------------------------------------
# 3. Side-by-Side Status & Metric Cards
# -------------------------------------------------------------------
st.subheader("Cluster Overview")

m1, m2, m3, m4 = st.columns(4)

with m1:
    render_metric_card(
        "Inference Latency",
        cluster_a_metrics["latency"],
        cluster_b_metrics["latency"],
        status_a=color_a,
        status_b=color_b,
    )

with m2:
    render_metric_card(
        "Error Rate",
        cluster_a_metrics["error_rate"],
        cluster_b_metrics["error_rate"],
        status_a=color_a,
        status_b=color_b,
    )

with m3:
    render_metric_card(
        "GPU Utilization",
        cluster_a_metrics["gpu_util"],
        cluster_b_metrics["gpu_util"],
        status_a=color_a,
        status_b=color_b,
    )

with m4:
    render_metric_card(
        "Queue Depth",
        cluster_a_metrics["queue_depth"],
        cluster_b_metrics["queue_depth"],
        status_a=color_a,
        status_b=color_b,
    )

st.divider()

# -------------------------------------------------------------------
# 4. Timeline Charts
# -------------------------------------------------------------------
st.subheader("Performance Timelines")
df_timeline = generate_timeline_data(incident)

c1, c2 = st.columns(2)

with c1:
    fig_gpu = create_timeline_chart(
        df_timeline,
        "Cluster A GPU Util",
        "Cluster B GPU Util",
        "GPU Utilization Over Time",
        "Utilization (%)",
    )
    st.plotly_chart(fig_gpu, use_container_width=True)

    fig_lat = create_timeline_chart(
        df_timeline,
        "Cluster A Latency",
        "Cluster B Latency",
        "Inference Latency Over Time",
        "Latency (ms)",
    )
    st.plotly_chart(fig_lat, use_container_width=True)

with c2:
    fig_queue = create_timeline_chart(
        df_timeline,
        "Cluster A Queue Depth",
        "Cluster B Queue Depth",
        "Queue Depth Over Time",
        "Requests in Queue",
    )
    st.plotly_chart(fig_queue, use_container_width=True)

    fig_err = create_timeline_chart(
        df_timeline,
        "Cluster A Error Rate",
        "Cluster B Error Rate",
        "Error Rate Over Time",
        "Error Rate (%)",
    )
    st.plotly_chart(fig_err, use_container_width=True)

st.divider()

# -------------------------------------------------------------------
# 5. Evidence & Investigation
# -------------------------------------------------------------------
st.subheader("Investigation Findings")

e1, e2, e3 = st.columns(3)

with e1:
    st.markdown("### 📊 Metrics Evidence")
    if incident:
        st.write("• **GPU Utilization:** Increased from 60% to 96%.")
        st.write("• **Queue Depth:** Increased from 20 to 180.")
        st.write("• **Latency:** Increased from 200 ms to 500 ms.")
    else:
        st.info("Metrics are within normal baseline levels.")

with e2:
    st.markdown("### 📜 Logs Evidence")
    if incident:
        st.write("• Timeout errors began after the queue increased.")
        st.write("• Multiple requests exceeded the latency limit.")
    else:
        st.info("No anomalous log events detected.")

with e3:
    st.markdown("### 🔍 Traces Evidence")
    if incident:
        st.write("• Requests spent longer waiting in Cluster A's queue.")
        st.write("• Cluster B continued processing normally.")
    else:
        st.info("Trace durations are nominal across all clusters.")

st.divider()

# -------------------------------------------------------------------
# 6. Root Cause & Recommendations
# -------------------------------------------------------------------
r_col1, r_col2 = st.columns(2)

with r_col1:
    st.markdown("### 🎯 Root Cause Analysis")
    if incident:
        st.error("**Root Cause:** GPU saturation in Cluster A")
        st.metric(label="Confidence Score", value="94%")
    else:
        st.success("**Root Cause:** No active incidents identified.")

with r_col2:
    st.markdown("### 💡 Recommended Action")
    if incident:
        st.warning("**Action:** Shift traffic from Cluster A to Cluster B.")

        if not st.session_state.recommendation_applied:
            st.button(
                "Apply Recommendation",
                on_click=apply_recommendation,
                type="primary",
            )
        else:
            st.success(
                "Recommendation applied successfully. Traffic is being shifted to Cluster B."
            )
    else:
        st.info("System healthy. No remediation needed.")

st.divider()

# -------------------------------------------------------------------
# 7. AI Executive Summary
# -------------------------------------------------------------------
st.subheader("🤖 AI Incident Report")

if incident:
    st.markdown(
        """
        > **Executive Summary:**
        > Cluster A became overloaded, reaching **96% GPU utilization**. This caused request queue buildup, increased inference latency, and timeout errors. Cluster B is healthy and has available capacity, so traffic should be shifted there.
        """
    )
else:
    st.markdown(
        """
        > **Executive Summary:**
        > All clusters are operating within operational thresholds. No resource bottlenecks or traffic routing anomalies observed.
        """
    )