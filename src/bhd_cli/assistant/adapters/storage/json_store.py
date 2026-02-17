"""JSON-based storage adapter (stub implementation)."""
import json
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

from ...core.entities import FindingDraft, Observation
from ...core.ports import IStoragePort


class JSONStorageAdapter(IStoragePort):
    """JSON file-based storage adapter."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.observations_file = storage_dir / "observations.jsonl"
        self.findings_file = storage_dir / "findings.jsonl"

    def save_observation(self, observation: Observation) -> str:
        """Save an observation and return its ID."""
        obs_data = observation.to_dict()

        # Append to JSONL file
        with open(self.observations_file, "a") as f:
            f.write(json.dumps(obs_data, sort_keys=True) + "\n")

        return observation.id

    def load_observations(self, session_id: str) -> List[Observation]:
        """Load observations for a session.

        Reconstructs Observation from to_dict() format.
        """
        # Stub: In a real implementation, filter by session_id
        observations = []

        if not self.observations_file.exists():
            return observations

        with open(self.observations_file) as f:
            for line in f:
                data = json.loads(line)
                # Convert category string back to enum
                from ...core.entities import ObservationCategory
                category = ObservationCategory(data["category"])

                obs = Observation(
                    id=data["id"],
                    source_artifact=data["source_artifact"],
                    category=category,
                    tags=data["tags"],
                    confidence=data["confidence"],
                    data=data["data"],
                    created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
                )
                observations.append(obs)

        return observations

    def save_finding_draft(self, draft: FindingDraft) -> str:
        """Save a finding draft and return its ID."""
        draft_data = draft.to_dict()
        draft_data["created_at"] = datetime.utcnow().isoformat()

        # Append to JSONL file
        with open(self.findings_file, "a") as f:
            f.write(json.dumps(draft_data, sort_keys=True) + "\n")

        return draft.id
