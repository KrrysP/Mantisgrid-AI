# MantisGuard Person A Backend & Person B Handoff Guide

MantisGuard is an evidence-first AI infrastructure root-cause investigator. This document provides the complete integration contract and handoff instructions for Person B to build the Streamlit dashboard.

---

## 1. Exact Import Statement

Person B should import the main investigation entry point directly from the pipeline:

```python
from pipeline.investigator import run_investigation
```

---

## 2. Exact Function Call

To execute the root-cause investigation:

```python
# Incident scenario (default)
result = run_investigation("cluster_a_overload")

# Healthy baseline scenario
result_healthy = run_investigation("healthy")
```

---

## 3. `InvestigationResult` Contract Fields

The object returned by `run_investigation()` is a typed Pydantic model (`InvestigationResult`).

| Field Name | Type | Description | Example Value |
|---|---|---|---|
| `incident_title` | `str` | Title summary for dashboard banner | `"CRITICAL: Inference Latency Spike & GPU Overload on cluster-a"` |
| `severity` | `str` | Overall severity (`INFO`, `WARN`, `ERROR`, `CRITICAL`) | `"CRITICAL"` |
| `affected_cluster` | `str` | Primary cluster experiencing failure | `"cluster-a"` |
| `root_cause` | `str` | Concise identified root cause | `"cluster-a overload caused by GPU saturation"` |
| `confidence` | `float` | Investigation confidence percentage (0.0 - 100.0) | `100.0` |
| `evidence` | `List[EvidenceItem]` | Telemetry evidence supporting diagnosis | `[EvidenceItem(...)]` |
| `correlated_timeline` | `List[Dict[str, Any]]` | Chronological unified event timeline | `[{"sequence_index": 1, ...}]` |
| `cluster_health` | `List[ClusterHealth]` | Health metrics summary per cluster | `[ClusterHealth(...)]` |
| `recommendation` | `Recommendation` | Actionable traffic shift recommendation | `Recommendation(...)` |
| `explanation` | `str` | AI summary report (or deterministic fallback) | `"Cluster A is overloaded..."` |

### Child Schema Attributes

#### `ClusterHealth`
- `cluster`: `str` (e.g. `"cluster-a"`)
- `gpu_utilization`: `float` (e.g. `96.0`)
- `queue_depth`: `int` (e.g. `76`)
- `p95_latency_ms`: `float` (e.g. `1850.0`)
- `error_rate`: `float` (e.g. `8.4`)
- `root_cause_score`: `float` (e.g. `100.0`)
- `health_status`: `str` (`"HEALTHY"`, `"DEGRADED"`, `"CRITICAL"`)

#### `Recommendation`
- `action`: `str` (e.g. `"shift traffic"`)
- `source_cluster`: `str` (e.g. `"cluster-a"`)
- `target_cluster`: `Optional[str]` (e.g. `"cluster-b"`)
- `traffic_percentage`: `Optional[float]` (e.g. `30.0`)
- `reason`: `str` (e.g. `"cluster-b has lower latency..."`)
- `safety_notes`: `str` (e.g. `"Simulated recommendation only..."`)

#### `EvidenceItem`
- `source_type`: `str` (`"metric"`, `"log"`, `"trace"`)
- `timestamp`: `datetime`
- `cluster`: `str`
- `description`: `str`
- `severity`: `str` (`"INFO"`, `"WARN"`, `"ERROR"`, `"CRITICAL"`)
- `value`: `Optional[float]`

---

## 4. Example Returned JSON

Person B can also convert the result to dictionary or JSON if needed: `result.model_dump()` or `result.model_dump_json()`.

```json
{
  "incident_title": "CRITICAL: Inference Latency Spike & GPU Overload on cluster-a",
  "severity": "CRITICAL",
  "affected_cluster": "cluster-a",
  "root_cause": "cluster-a overload caused by GPU saturation",
  "confidence": 100.0,
  "evidence": [
    {
      "source_type": "log",
      "timestamp": "2026-09-16T10:00:32Z",
      "cluster": "cluster-a",
      "description": "Log alert (ERROR): P95 inference latency severe degradation: 1850ms",
      "severity": "ERROR",
      "value": null
    },
    {
      "source_type": "metric",
      "timestamp": "2026-09-16T10:00:45Z",
      "cluster": "cluster-a",
      "description": "GPU utilization reached 96.0% on cluster-a (exceeded 90% critical threshold)",
      "severity": "CRITICAL",
      "value": 96.0
    }
  ],
  "correlated_timeline": [
    {
      "sequence_index": 1,
      "timestamp": "2026-09-16T10:00:02Z",
      "cluster": "cluster-a",
      "service": "vllm-inference",
      "event_type": "log",
      "severity": "WARN",
      "description": "Log entry (WARN): GPU utilization exceeded 90% threshold (96.0% current)",
      "trace_id": "tr-001"
    }
  ],
  "cluster_health": [
    {
      "cluster": "cluster-a",
      "gpu_utilization": 96.0,
      "queue_depth": 76,
      "p95_latency_ms": 1850.0,
      "error_rate": 8.4,
      "root_cause_score": 100.0,
      "health_status": "CRITICAL"
    },
    {
      "cluster": "cluster-b",
      "gpu_utilization": 57.0,
      "queue_depth": 18,
      "p95_latency_ms": 410.0,
      "error_rate": 0.7,
      "root_cause_score": 0.0,
      "health_status": "HEALTHY"
    }
  ],
  "recommendation": {
    "action": "shift traffic",
    "source_cluster": "cluster-a",
    "target_cluster": "cluster-b",
    "traffic_percentage": 30.0,
    "reason": "cluster-b has lower latency, fewer errors, and available capacity to absorb workload from overloaded cluster-a.",
    "safety_notes": "Simulated recommendation only. Verify target cluster capacity before execution."
  },
  "explanation": "Cluster A is overloaded. GPU utilization reached 96 percent, causing queue growth. This was followed by increased inference latency and timeout errors. Cluster B remained healthy, so traffic should be shifted from Cluster A to Cluster B. Confidence is high."
}
```

---

## 5. How to Handle Loading & Errors in Streamlit

In Streamlit, wrap the pipeline call with `st.spinner` and a `try-except` block:

```python
import streamlit as st
from pipeline.investigator import run_investigation

try:
    with st.spinner("Analyzing cluster telemetry and running root-cause investigation..."):
        result = run_investigation("cluster_a_overload")
except Exception as e:
    st.error(f"Investigation Engine Failed: {e}")
```

---

## 6. Dashboard Metrics Mapping

Person B should map backend fields to visual components as follows:

| UI Widget | Backend Attribute | Display Format / Notes |
|---|---|---|
| **Incident Banner** | `result.incident_title` | Header banner text |
| **Severity Badge** | `result.severity` | Red for CRITICAL, Yellow for WARN, Green for INFO |
| **KPI Metric 1** | `result.affected_cluster` | Label: "Affected Cluster" |
| **KPI Metric 2** | `result.root_cause` | Label: "Identified Root Cause" |
| **KPI Metric 3** | `result.confidence` | Format: `f"{result.confidence:.1f}%"` |
| **Cluster Cards** | `result.cluster_health` | Iterate through list to build comparison cards or table |
| **Card GPU%** | `ch.gpu_utilization` | Format: `f"{ch.gpu_utilization:.1f}%"` |
| **Card Queue** | `ch.queue_depth` | Format: `f"{ch.queue_depth}"` |
| **Card Latency** | `ch.p95_latency_ms` | Format: `f"{ch.p95_latency_ms:.1f} ms"` |
| **Card Error Rate**| `ch.error_rate` | Format: `f"{ch.error_rate:.1f}%"` |
| **Recommendation Box** | `result.recommendation` | Display Action, Source, Target, Traffic %, Reason & Safety Notes |
| **AI Summary Text**| `result.explanation` | Markdown or text block displaying natural language report |

---

## 7. Timeline Display Guidance

Use `result.correlated_timeline` or `result.evidence` to build the Streamlit incident timeline:

```python
st.subheader("Unified Telemetry Timeline")

for event in result.correlated_timeline:
    st.markdown(
        f"**Step {event.get('sequence_index', '')}** | `{event['timestamp']}` | "
        f"**{event['cluster']}** | `{event['severity']}` | {event['description']}"
    )
```

---

## 8. Triggering via "Simulate Incident" Button

Use `st.session_state` to store investigation results when buttons are clicked:

```python
import streamlit as st
from pipeline.investigator import run_investigation

st.sidebar.title("MantisGuard Simulation Controls")

col1, col2 = st.sidebar.columns(2)
if col1.button("Simulate Incident"):
    st.session_state["investigation_result"] = run_investigation("cluster_a_overload")

if col2.button("Run Baseline"):
    st.session_state["investigation_result"] = run_investigation("healthy")

# Retrieve current result (default to cluster_a_overload if not set)
if "investigation_result" not in st.session_state:
    st.session_state["investigation_result"] = run_investigation("cluster_a_overload")

result = st.session_state["investigation_result"]

# Render dashboard using result object...
```
