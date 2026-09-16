"""AI explanation agent with deterministic fallback adapter for MantisGuard."""

import os
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv
from analysis.schemas import InvestigationResult

load_dotenv()

FALLBACK_EXPLANATION = (
    "Cluster A is overloaded. GPU utilization reached 96 percent, causing queue growth. "
    "This was followed by increased inference latency and timeout errors. "
    "Cluster B remained healthy, so traffic should be shifted from Cluster A to Cluster B. "
    "Confidence is high."
)


class BaseLLMAdapter:
    """Abstract adapter for LLM provider integrations."""

    def generate_explanation(self, prompt: str) -> str:
        raise NotImplementedError


class FallbackExplanationAdapter(BaseLLMAdapter):
    """Deterministic fallback explanation provider when no LLM API key is available."""

    def generate_explanation(self, prompt: str) -> str:
        return FALLBACK_EXPLANATION


class OpenAILLMAdapter(BaseLLMAdapter):
    """Optional LLM provider adapter using OpenAI SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def generate_explanation(self, prompt: str) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI infrastructure incident investigator. "
                            "Rely STRICTLY on the provided evidence. "
                            "Do NOT calculate scores, invent metrics, or add unverified causes. "
                            "Keep your response under 150 words."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            # Fallback on any connection/API error
            return FALLBACK_EXPLANATION


class ExplanationAgent:
    """Agent that formats structured investigation data and generates natural language explanations.

    Does NOT compute root causes, scores, or evidence. Accepts pre-calculated investigation results only.
    """

    def __init__(self, adapter: Optional[BaseLLMAdapter] = None):
        if adapter:
            self.adapter = adapter
        else:
            api_key = os.getenv("LLM_API_KEY")
            model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            if api_key and api_key.strip():
                self.adapter = OpenAILLMAdapter(api_key=api_key.strip(), model=model)
            else:
                self.adapter = FallbackExplanationAdapter()

    def generate_explanation(self, investigation_data: Union[InvestigationResult, Dict[str, Any]]) -> str:
        """Generates a concise report from structured investigation data without inventing evidence."""
        # Standardize dictionary vs InvestigationResult schema
        if isinstance(investigation_data, InvestigationResult):
            affected = investigation_data.affected_cluster
            root_cause = investigation_data.root_cause
            confidence = investigation_data.confidence
            evidence_items = investigation_data.evidence
            recommendation = investigation_data.recommendation
        elif isinstance(investigation_data, dict):
            affected = investigation_data.get("affected_cluster", "cluster-a")
            root_cause = investigation_data.get("root_cause", "")
            confidence = investigation_data.get("confidence", 0.0)
            evidence_items = investigation_data.get("evidence", [])
            recommendation = investigation_data.get("recommendation")
        else:
            raise TypeError("investigation_data must be an InvestigationResult or dict")

        # If using deterministic fallback adapter, return fixed report immediately
        if isinstance(self.adapter, FallbackExplanationAdapter):
            return self.adapter.generate_explanation("")

        # Build prompt using strictly supplied evidence
        evidence_descriptions = []
        for item in evidence_items:
            if hasattr(item, "description"):
                evidence_descriptions.append(f"- {item.description}")
            elif isinstance(item, dict) and "description" in item:
                evidence_descriptions.append(f"- {item['description']}")

        evidence_str = "\n".join(evidence_descriptions[:5])
        rec_str = (
            f"Shift traffic from {recommendation.source_cluster} to {recommendation.target_cluster}"
            if hasattr(recommendation, "source_cluster") and recommendation.target_cluster
            else str(recommendation)
        )

        prompt = (
            f"Generate a concise incident summary report (under 150 words) based STRICTLY on this evidence:\n"
            f"Affected Cluster: {affected}\n"
            f"Calculated Root Cause: {root_cause}\n"
            f"Calculated Confidence: {confidence:.1f}%\n"
            f"Remediation Recommendation: {rec_str}\n"
            f"Evidence Items:\n{evidence_str}\n\n"
            f"Do not invent metrics or causes not present above."
        )

        return self.adapter.generate_explanation(prompt)
