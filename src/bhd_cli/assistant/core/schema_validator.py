"""Schema validation for all structured outputs."""
import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


class SchemaValidator:
    """Validates data against JSON schemas."""

    def __init__(self, schemas_dir: Optional[Path] = None):
        if not JSONSCHEMA_AVAILABLE:
            raise ImportError("jsonschema library required: pip install jsonschema")

        if schemas_dir is None:
            schemas_dir = Path(__file__).parent.parent / "schemas"

        self.schemas_dir = schemas_dir
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    def _load_schema(self, schema_name: str) -> Dict[str, Any]:
        """Load a schema from file."""
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        schema_file = self.schemas_dir / f"{schema_name}.schema.json"
        if not schema_file.exists():
            # Try playbooks schemas dir
            schema_file = self.schemas_dir.parent / "playbooks" / "schemas" / f"{schema_name}.schema.json"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema not found: {schema_name}")

        with open(schema_file) as f:
            schema = json.load(f)

        self._schema_cache[schema_name] = schema
        return schema

    def validate(self, data: Dict[str, Any], schema_name: str) -> bool:
        """Validate data against schema.

        Args:
            data: Data to validate
            schema_name: Name of schema (without .schema.json)

        Returns:
            True if valid

        Raises:
            jsonschema.ValidationError: If validation fails
        """
        schema = self._load_schema(schema_name)
        jsonschema.validate(data, schema)
        return True

    def validate_observation(self, data: Dict[str, Any]) -> bool:
        """Validate observation data."""
        return self.validate(data, "observation")

    def validate_hypothesis(self, data: Dict[str, Any]) -> bool:
        """Validate hypothesis data."""
        return self.validate(data, "hypothesis")

    def validate_evidence_plan(self, data: Dict[str, Any]) -> bool:
        """Validate evidence plan data."""
        return self.validate(data, "evidence")

    def validate_finding_draft(self, data: Dict[str, Any]) -> bool:
        """Validate finding draft data."""
        return self.validate(data, "finding_draft")

    def validate_export_bundle(self, data: Dict[str, Any]) -> bool:
        """Validate export bundle data."""
        schema_file = self.schemas_dir.parent / "integration" / "bhd_cli" / "schemas" / "bundle.schema.json"
        with open(schema_file) as f:
            schema = json.load(f)
        jsonschema.validate(data, schema)
        return True


# Global validator instance
_validator: Optional[SchemaValidator] = None


def get_validator() -> SchemaValidator:
    """Get or create global schema validator."""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator
