"""Playbook selector based on observations and rules."""
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        test_type: str
    ) -> Optional[str]:
        """Select appropriate playbook based on observations and test type."""
        matching_rules = []

        for rule in self.rules.get("rules", []):
            # Check if test type matches
            if test_type not in rule.get("test_types", []):
                continue

            # Check if observations match rule conditions
            if self._matches_conditions(observations, rule.get("conditions", [])):
                matching_rules.append((rule["priority"], rule["playbook_id"]))

        if not matching_rules:
            return self.rules.get("default_playbook")

        # Return highest priority match
        matching_rules.sort(key=lambda x: x[0], reverse=True)
        return matching_rules[0][1]

    def _matches_conditions(
        self,
        observations: List[Observation],
        conditions: List[Dict[str, Any]]
    ) -> bool:
        """Check if observations match all conditions."""
        if not conditions:
            return False

        for condition in conditions:
            category = condition.get("category")
            data_contains = condition.get("data_contains", [])

            # Find observations of matching category
            matching_obs = [
                obs for obs in observations
                if obs.category.value == category
            ]

            if not matching_obs:
                return False

            # Check if any matching observation satisfies data_contains
            satisfied = False
            for obs in matching_obs:
                if self._check_data_contains(obs.data, data_contains):
                    satisfied = True
                    break

            if not satisfied:
                return False

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
