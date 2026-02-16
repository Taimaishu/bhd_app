"""
Storage abstraction layer for bhd-cli.

Currently uses JSON file backend. Designed to support SQLite backend in future
without changing CLI behavior or command structure.

Architecture:
- EngagementStorage: Abstract interface for all storage operations
- JSONStorage: Current implementation using engagement.json files
- Future: SQLiteStorage can be plugged in without breaking changes
"""
import json
from pathlib import Path
from typing import Optional


class EngagementStorage:
    """
    Abstract storage interface for engagement data.

    All engagement data operations should go through this interface to
    enable future backend migrations (e.g., JSON -> SQLite) without
    breaking CLI commands or behavior.
    """

    def load(self, engagement_path: Path) -> dict:
        """Load engagement data from storage."""
        raise NotImplementedError

    def save(self, engagement_path: Path, data: dict) -> None:
        """Save engagement data to storage."""
        raise NotImplementedError

    def export_json(self, engagement_path: Path, export_path: Path) -> None:
        """Export engagement data to a standalone JSON file."""
        raise NotImplementedError


class JSONStorage(EngagementStorage):
    """
    JSON file-based storage backend (current implementation).

    Stores engagement data in engagement.json files within each
    engagement folder. Maintains backwards compatibility with existing
    data format.
    """

    def load(self, engagement_path: Path) -> dict:
        """
        Load engagement data from engagement.json.

        Args:
            engagement_path: Path to engagement folder

        Returns:
            Dictionary with engagement data, or empty dict if file doesn't exist
        """
        f = engagement_path / "engagement.json"
        if not f.exists():
            return {}
        return json.loads(f.read_text())

    def save(self, engagement_path: Path, data: dict) -> None:
        """
        Save engagement data to engagement.json.

        Args:
            engagement_path: Path to engagement folder
            data: Engagement data dictionary
        """
        f = engagement_path / "engagement.json"
        # Preserve deterministic output: indent=2, but don't sort keys globally
        # (preserve insertion order for better readability)
        f.write_text(json.dumps(data, indent=2, sort_keys=False))

    def export_json(self, engagement_path: Path, export_path: Path) -> None:
        """
        Export engagement data to a standalone JSON file.

        Creates a clean export with deterministic ordering suitable for
        archival or sharing with clients.

        Args:
            engagement_path: Path to engagement folder
            export_path: Path where export.json should be written
        """
        data = self.load(engagement_path)

        # Create export with explicit key ordering for determinism
        export = {}

        # Metadata section
        if "meta" in data:
            export["meta"] = data["meta"]

        # Scope section
        if "scope" in data:
            export["scope"] = data["scope"]

        # Methodology section
        if "methodology" in data:
            export["methodology"] = data["methodology"]

        # Work section (notes + findings)
        export["work"] = {}
        if "notes" in data:
            export["work"]["notes"] = data["notes"]
        if "findings" in data:
            # Sort findings by ID for deterministic output
            findings = data["findings"]
            sorted_findings = sorted(
                findings,
                key=lambda f: self._finding_sort_key(f)
            )
            export["work"]["findings"] = sorted_findings

        # Write with sorted keys for deterministic output
        export_path.write_text(json.dumps(export, indent=2, sort_keys=True))

    @staticmethod
    def _finding_sort_key(f: dict) -> float:
        """
        Extract numeric ID from finding for sorting (F-001 -> 1, F-023 -> 23).
        Returns float("inf") for malformed IDs (sorts them last).
        """
        import re
        fid = f.get("id", "")
        m = re.match(r"^F-(\d+)$", fid)
        return int(m.group(1)) if m else float("inf")


# Global storage instance (currently JSON, can be swapped for SQLite later)
storage = JSONStorage()
