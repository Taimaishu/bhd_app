"""Hypothesis drafting service with schema validation and repair."""
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema

from .adaptive_mode import AssistContext, EffectiveAssistLevel, evaluate_assist_level
from .entities import Hypothesis, Observation
from .ports import ILLMPort, IPolicyGuard


logger = logging.getLogger(__name__)


class HypothesisDrafter:
    """Service for drafting hypotheses from observations using LLM."""

    def __init__(
        self,
        llm_provider: ILLMPort,
        policy_guard: IPolicyGuard,
        schema_path: Optional[Path] = None
    ):
        self.llm = llm_provider
        self.policy_guard = policy_guard

        # Load hypothesis schema
        if schema_path is None:
            schema_path = Path(__file__).parent.parent / "schemas" / "hypothesis.schema.json"

        with open(schema_path) as f:
            self.schema = json.load(f)

    def draft_hypotheses(
        self,
        observations: List[Observation],
        context: AssistContext,
        max_hypotheses: int = 3
    ) -> Dict[str, Any]:
        """
        Draft hypotheses from observations.

        Returns:
            Dict with keys:
            - status: "success" or "error"
            - effective_assist_level: str
            - reasons: List[str]
            - provider_used: str (if successful)
            - hypotheses: List[Dict] (if successful)
            - error: str (if error)
        """
        # Evaluate effective assistance level
        evaluation = evaluate_assist_level(context)

        # Group observations (simple heuristic: by category + host)
        clusters = self._cluster_observations(observations)

        # Generate hypotheses for each cluster (up to max_hypotheses)
        hypotheses = []
        for i, cluster in enumerate(clusters[:max_hypotheses]):
            try:
                hyp = self._draft_single_hypothesis(
                    cluster,
                    evaluation.effective_level
                )
                if hyp:
                    hypotheses.append(hyp.to_dict())
            except Exception as e:
                logger.error(f"Failed to draft hypothesis for cluster {i}: {e}")
                continue

        # Get provider name if available
        provider_used = None
        if hasattr(self.llm, 'get_last_used_provider'):
            provider_used = self.llm.get_last_used_provider()

        return {
            "status": "success",
            "effective_assist_level": evaluation.effective_level.value,
            "reasons": evaluation.reasons,
            "provider_used": provider_used,
            "hypotheses": hypotheses
        }

    def _cluster_observations(self, observations: List[Observation]) -> List[List[Observation]]:
        """
        Cluster observations by category and host.

        Simple heuristic: group by (category, host) where host exists in data.
        """
        clusters: Dict[Tuple[str, str], List[Observation]] = {}

        for obs in observations:
            category = obs.category.value if hasattr(obs.category, 'value') else str(obs.category)
            host = obs.data.get("host", obs.data.get("hostname", "unknown"))
            key = (category, host)

            if key not in clusters:
                clusters[key] = []
            clusters[key].append(obs)

        return list(clusters.values())

    def _draft_single_hypothesis(
        self,
        observations: List[Observation],
        assist_level: EffectiveAssistLevel
    ) -> Optional[Hypothesis]:
        """Draft a single hypothesis from clustered observations."""
        # Build prompt
        prompt = self._build_prompt(observations, assist_level)

        # Try to generate with repair loop (up to 2 repair attempts)
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                if attempt == 0:
                    # First attempt: normal prompt
                    result = self.llm.generate_structured(
                        prompt,
                        self.schema,
                        temperature=0.0
                    )
                else:
                    # Repair attempt: include validation error
                    repair_prompt = f"""{prompt}

PREVIOUS ATTEMPT FAILED VALIDATION:
{last_error}

Please provide a corrected JSON response that exactly matches the schema."""
                    result = self.llm.generate_structured(
                        repair_prompt,
                        self.schema,
                        temperature=0.0
                    )

                # Validate against schema
                jsonschema.validate(instance=result, schema=self.schema)

                # Policy guard check on text fields
                text_content = "\n".join([
                    result.get("title", ""),
                    result.get("description", ""),
                    result.get("rationale", "")
                ])

                if not self.policy_guard.check_content(text_content, {"source": "hypothesis_draft"}):
                    logger.warning("Hypothesis blocked by policy guard")
                    return None

                # Convert to Hypothesis entity
                return Hypothesis(
                    id=result["id"],
                    related_observations=result["related_observations"],
                    title=result["title"],
                    description=result["description"],
                    risk_tags=result["risk_tags"],
                    confidence=result["confidence"],
                    rationale=result["rationale"],
                    requires_validation=result.get("requires_validation", True)
                )

            except jsonschema.ValidationError as e:
                last_error = str(e)
                logger.warning(f"Schema validation failed (attempt {attempt + 1}): {e}")
                if attempt == max_attempts - 1:
                    logger.error("Max repair attempts reached, giving up")
                    return None
                continue
            except Exception as e:
                logger.error(f"Unexpected error drafting hypothesis: {e}")
                return None

        return None

    def _build_prompt(
        self,
        observations: List[Observation],
        assist_level: EffectiveAssistLevel
    ) -> str:
        """Build prompt for hypothesis generation."""
        # Serialize observations
        obs_text = "\n".join([
            f"Observation {obs.id}:\n"
            f"  Category: {obs.category.value if hasattr(obs.category, 'value') else obs.category}\n"
            f"  Tags: {', '.join(obs.tags)}\n"
            f"  Data: {json.dumps(obs.data, indent=2)}\n"
            f"  Confidence: {obs.confidence}"
            for obs in observations
        ])

        # Get observation IDs for reference
        obs_ids = [obs.id for obs in observations]

        # Generate deterministic hypothesis ID
        obs_ids_str = "-".join(sorted(obs_ids))
        hyp_id = hashlib.sha256(obs_ids_str.encode()).hexdigest()[:16]

        # Build prompt based on assistance level
        if assist_level == EffectiveAssistLevel.DEEP_LAB:
            constraints = """
Safety Constraints (LAB MODE):
- Focus on validation techniques and evidence collection
- Provide testing methodologies appropriate for lab environments
- Include risk framing and threat modeling
- Suggest safe verification strategies
- DO NOT provide actual exploit code or weaponized payloads
- DO NOT provide bypass steps or persistence mechanisms
- Cite observation IDs in the rationale
"""
        else:  # STANDARD
            constraints = """
Safety Constraints (STANDARD MODE):
- Focus ONLY on validation checklists and evidence collection
- Provide safe, non-destructive testing guidance
- Include risk framing suitable for client environments
- DO NOT provide exploitation guidance
- DO NOT provide exploit code, payloads, or bypass instructions
- Cite observation IDs in the rationale
"""

        prompt = f"""Based on the following observations, draft a security hypothesis.

Observations:
{obs_text}

{constraints}

Generate a JSON hypothesis with:
- id: "{hyp_id}"
- related_observations: {json.dumps(obs_ids)}
- title: Short hypothesis title (max 100 chars)
- description: Technical description of the potential security issue (2-4 sentences)
- risk_tags: List of relevant risk tags (e.g., ["exposure", "misconfiguration", "authentication"])
- confidence: Float 0-1 representing confidence in this hypothesis
- rationale: Why this hypothesis was formed based on the observations (cite observation IDs)
- requires_validation: boolean (default true)

Output ONLY valid JSON matching the schema. No markdown formatting."""

        return prompt
