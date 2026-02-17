#!/usr/bin/env python3
"""Validate playbooks against JSON schema."""
import json
import sys
from pathlib import Path

try:
    import jsonschema
    import yaml
except ImportError:
    print("Missing dependencies: pip install jsonschema pyyaml")
    sys.exit(1)


def validate_playbooks():
    """Validate all playbooks against schema."""
    base_dir = Path(__file__).parent.parent
    playbooks_dir = base_dir / "src" / "bhd_cli" / "assistant" / "playbooks" / "library"
    schema_file = base_dir / "src" / "bhd_cli" / "assistant" / "playbooks" / "schemas" / "playbook.schema.json"

    if not schema_file.exists():
        print(f"Schema file not found: {schema_file}")
        return False

    with open(schema_file) as f:
        schema = json.load(f)

    errors = []
    for playbook_file in playbooks_dir.glob("*.yaml"):
        try:
            with open(playbook_file) as f:
                playbook_data = yaml.safe_load(f)

            jsonschema.validate(playbook_data, schema)
            print(f"✓ {playbook_file.name}")
        except jsonschema.ValidationError as e:
            errors.append(f"✗ {playbook_file.name}: {e.message}")
        except Exception as e:
            errors.append(f"✗ {playbook_file.name}: {e}")

    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  {error}")
        return False

    print(f"\n✓ All playbooks valid ({len(list(playbooks_dir.glob('*.yaml')))} checked)")
    return True


if __name__ == "__main__":
    success = validate_playbooks()
    sys.exit(0 if success else 1)
