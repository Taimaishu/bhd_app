"""Playbook selector based on observations and rules."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..core.entities import Observation


class PlaybookSelector:
    """Selects appropriate playbook based on observations and rules."""

    def __init__(self, rules_path: Path):
        self.rules_path = rules_path
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Load selector rules from YAML."""
        with open(self.rules_path) as f:
            return yaml.safe_load(f)

    def select_playbook(
        self,
        observations: List[Observation],
        test_type: str,
        explain: bool = False
    ) -> Union[Optional[str], Dict[str, Any]]:
        """Select appropriate playbook based on observations and test type.

        Args:
            observations: List of observations to evaluate
            test_type: Type of test (web, network, ics, etc.)
            explain: If True, return detailed evaluation info

        Returns:
            If explain=False: playbook_id (str) or None
            If explain=True: dict with evaluated_rules and selected_playbook
        """
        matching_rules = []
        evaluated_rules = [] if explain else None

        for rule in self.rules.get("rules", []):
            rule_id = rule.get("id", "unknown")

            # Check if test type matches
            if test_type not in rule.get("test_types", []):
                if explain:
                    evaluated_rules.append({
                        "rule_id": rule_id,
                        "matched": False,
                        "failure_reasons": [f"test_type '{test_type}' not in rule test_types {rule.get('test_types', [])}"]
                    })
                continue

            # Check if observations match rule conditions
            match_result = self._matches_conditions(
                observations,
                rule.get("conditions", []),
                explain=explain
            )

            if explain:
                matched, failure_reasons = match_result
            else:
                matched = match_result
                failure_reasons = []

            if matched:
                matching_rules.append((rule["priority"], rule["playbook_id"]))
                if explain:
                    evaluated_rules.append({
                        "rule_id": rule_id,
                        "matched": True,
                        "priority": rule["priority"],
                        "playbook_id": rule["playbook_id"]
                    })
            elif explain:
                evaluated_rules.append({
                    "rule_id": rule_id,
                    "matched": False,
                    "failure_reasons": failure_reasons
                })

        selected_playbook = None
        if matching_rules:
            # Return highest priority match
            matching_rules.sort(key=lambda x: x[0], reverse=True)
            selected_playbook = matching_rules[0][1]
        else:
            selected_playbook = self.rules.get("default_playbook")

        if explain:
            return {
                "evaluated_rules": evaluated_rules,
                "selected_playbook": selected_playbook
            }
        else:
            return selected_playbook

    def _matches_conditions(
        self,
        observations: List[Observation],
        conditions: List[Dict[str, Any]],
        explain: bool = False
    ) -> Union[bool, tuple]:
        """Check if observations match all conditions.

        Args:
            observations: List of observations to check
            conditions: List of condition dicts to evaluate
            explain: If True, return (matched, failure_reasons)

        Returns:
            If explain=False: bool
            If explain=True: (bool, List[str])
        """
        if not conditions:
            if explain:
                return (False, ["No conditions specified"])
            return False

        failure_reasons = [] if explain else None

        for idx, condition in enumerate(conditions):
            category = condition.get("category")
            data_contains = condition.get("data_contains", [])

            # Find observations of matching category
            matching_obs = [
                obs for obs in observations
                if obs.category.value == category
            ]

            if not matching_obs:
                if explain:
                    failure_reasons.append(
                        f"Condition {idx}: No observations with category '{category}' "
                        f"(available: {list(set(obs.category.value for obs in observations))})"
                    )
                    return (False, failure_reasons)
                return False

            # Check if any matching observation satisfies data_contains
            satisfied = False
            for obs in matching_obs:
                if self._check_data_contains(obs.data, data_contains):
                    satisfied = True
                    break

            if not satisfied:
                if explain:
                    failure_reasons.append(
                        f"Condition {idx}: Found {len(matching_obs)} observation(s) with category '{category}', "
                        f"but none satisfied data_contains requirements: {data_contains}"
                    )
                    return (False, failure_reasons)
                return False

        if explain:
            return (True, [])
        return True

    def _check_data_contains(
        self,
        data: Dict[str, Any],
        requirements: List[Dict[str, Any]]
    ) -> bool:
        """Check if data contains all required fields and values."""
        for req in requirements:
            key = req.get("key")
            if key not in data:
                return False

            if "value" in req:
                if data[key] != req["value"]:
                    return False

            if "values" in req:
                if data[key] not in req["values"]:
                    return False

            if "contains" in req:
                data_str = str(data[key]).lower()
                if not any(substr.lower() in data_str for substr in req["contains"]):
                    return False

        return True
