# MantisGuard

MantisGuard is an evidence-first root-cause investigator for AI inference infrastructure.

It analyzes simulated GPU, queue, latency, log, and trace data to identify why an inference cluster became unhealthy. It then provides supporting evidence and recommends a corrective action, such as shifting traffic to a healthier cluster.

## What MantisGuard Does

Given a scenario, MantisGuard:

1. Loads metrics, logs, and traces.
2. Detects abnormal infrastructure behavior.
3. Correlates events across a timeline.
4. Scores possible root causes.
5. Calculates a confidence score.
6. Compares cluster health.
7. Recommends an action.
8. Generates a plain-language incident explanation.

The canonical incident is:

```text
GPU saturation on cluster-a
→ queue growth
→ increased P95 latency
→ timeout and error increase
→ recommend shifting traffic to cluster-b