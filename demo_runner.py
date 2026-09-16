"""Demo runner script for MantisGuard root-cause investigation engine."""

import sys
from pipeline.investigator import run_investigation

# Ensure stdout uses utf-8 encoding on Windows terminals
sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("=" * 70)
    print(" 🛡️  MANTISGUARD: AI INFRASTRUCTURE ROOT-CAUSE INVESTIGATOR DEMO")
    print("=" * 70)
    print("Running end-to-end investigation on 'cluster_a_overload' scenario...\n")

    result = run_investigation("cluster_a_overload")

    print(f"📌 INCIDENT TITLE    : {result.incident_title}")
    print(f"🚨 SEVERITY          : {result.severity}")
    print(f"🎯 AFFECTED CLUSTER  : {result.affected_cluster}")
    print(f"🔍 ROOT CAUSE        : {result.root_cause}")
    print(f"💯 CONFIDENCE        : {result.confidence:.1f}%\n")

    print("-" * 70)
    print("📊 CLUSTER HEALTH COMPARISON:")
    print("-" * 70)
    for ch in result.cluster_health:
        print(
            f"  • Cluster: {ch.cluster:<10} | Status: {ch.health_status:<8} | "
            f"GPU: {ch.gpu_utilization:4.1f}% | Queue: {ch.queue_depth:2d} | "
            f"P95 Latency: {ch.p95_latency_ms:6.1f}ms | Error Rate: {ch.error_rate:3.1f}% | "
            f"Root Cause Score: {ch.root_cause_score:4.1f}"
        )

    print("\n" + "-" * 70)
    print("📋 DETECTED TELEMETRY EVIDENCE:")
    print("-" * 70)
    for idx, item in enumerate(result.evidence, 1):
        print(f"  [{idx}] [{item.source_type.upper():<6}] [{item.severity:<8}] {item.description}")

    print("\n" + "-" * 70)
    print("💡 REMEDIATION RECOMMENDATION:")
    print("-" * 70)
    rec = result.recommendation
    print(f"  • Action             : {rec.action.upper()}")
    print(f"  • Source Cluster     : {rec.source_cluster}")
    print(f"  • Target Cluster     : {rec.target_cluster}")
    print(f"  • Suggested Shift    : {rec.traffic_percentage}% traffic")
    print(f"  • Reason             : {rec.reason}")
    print(f"  • Safety Notes       : {rec.safety_notes}")

    print("\n" + "-" * 70)
    print("🤖 AI EXPLANATION REPORT:")
    print("-" * 70)
    print(f"  \"{result.explanation}\"\n")
    print("=" * 70)
    print(" Investigation pipeline completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
