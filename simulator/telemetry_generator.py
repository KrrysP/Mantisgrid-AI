"""Telemetry generator and replay utilities for MantisGuard simulator."""

from typing import Dict, List, Tuple, Union
from analysis.schemas import MetricEvent, LogEvent, TraceEvent
from simulator.incident_scenarios import get_healthy_scenario, get_cluster_a_overload_scenario


def load_scenario(scenario_name: str = "cluster_a_overload") -> Dict[str, List]:
    """Loads a named telemetry scenario deterministically."""
    if scenario_name == "healthy":
        return get_healthy_scenario()
    elif scenario_name == "cluster_a_overload":
        return get_cluster_a_overload_scenario()
    else:
        raise ValueError(f"Unknown scenario name: '{scenario_name}'. Available: 'healthy', 'cluster_a_overload'.")


def get_all_telemetry(scenario_name: str = "cluster_a_overload") -> Tuple[List[MetricEvent], List[LogEvent], List[TraceEvent], List[MetricEvent]]:
    """Returns baseline metrics, incident metrics, logs, and traces for a scenario."""
    scenario = load_scenario(scenario_name)
    return (
        scenario["baseline_metrics"],
        scenario["metrics"],
        scenario["logs"],
        scenario["traces"],
    )


def replay_events(scenario_name: str = "cluster_a_overload") -> List[Union[MetricEvent, LogEvent, TraceEvent]]:
    """Returns all telemetry events combined and sorted strictly in chronological timestamp order."""
    _, metrics, logs, traces = get_all_telemetry(scenario_name)
    combined: List[Union[MetricEvent, LogEvent, TraceEvent]] = []
    combined.extend(metrics)
    combined.extend(logs)
    combined.extend(traces)
    combined.sort(key=lambda event: event.timestamp)
    return combined
