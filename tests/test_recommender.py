"""Unit tests for recommendation engine and cluster health assessment."""

from simulator.telemetry_generator import get_all_telemetry
from recommendation.recommender import (
    calculate_cluster_health,
    select_healthiest_cluster,
    generate_recommendation,
)


def test_cluster_b_selected_as_healthiest_target():
    _, metrics, _, _ = get_all_telemetry("cluster_a_overload")
    scores = {"cluster-a": 100.0, "cluster-b": 0.0}

    health_list = calculate_cluster_health(metrics, root_cause_scores=scores)
    target = select_healthiest_cluster(health_list, exclude_cluster="cluster-a")

    assert target == "cluster-b"


def test_recommendation_contains_cluster_a_and_cluster_b():
    _, metrics, _, _ = get_all_telemetry("cluster_a_overload")
    scores = {"cluster-a": 100.0, "cluster-b": 0.0}

    health_list = calculate_cluster_health(metrics, root_cause_scores=scores)
    rec = generate_recommendation("cluster-a", "cluster-a overload caused by GPU saturation", health_list)

    assert rec.action == "shift traffic"
    assert rec.source_cluster == "cluster-a"
    assert rec.target_cluster == "cluster-b"
    assert rec.traffic_percentage == 30.0
