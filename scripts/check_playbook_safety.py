#!/usr/bin/env python3
"""Check playbooks for required safety constraints."""
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pip install pyyaml")
    sys.exit(1)


REQUIRED_SAFETY_KEYWORDS = [
    "DO NOT",
    "authorization",
    "written",
]


def check_safety_constraints():
    """Check all playbooks have safety constraints."""
    base_dir = Path(__file__).parent.parent
    playbooks_dir = base_dir / "src" / "bhd_cli" / "assistant" / "playbooks" / "library"

    errors = []
    for playbook_file in playbooks_dir.glob("*.yaml"):
        try:
            with open(playbook_file) as f:
                playbook_data = yaml.safe_load(f)

            # Check safety_constraints field exists
            if "safety_constraints" not in playbook_data:
                errors.append(f"✗ {playbook_file.name}: Missing safety_constraints field")
                continue

            constraints = playbook_data["safety_constraints"]
            if not constraints or len(constraints) < 3:
                errors.append(f"✗ {playbook_file.name}: Insufficient safety constraints (minimum 3)")
                continue

            # Check for DO NOT constraints
            has_do_not = any("DO NOT" in str(c) for c in constraints)
            if not has_do_not:
                errors.append(f"✗ {playbook_file.name}: Missing 'DO NOT' constraints")

            print(f"✓ {playbook_file.name} ({len(constraints)} safety constraints)")

        except Exception as e:
            errors.append(f"✗ {playbook_file.name}: {e}")

    if errors:
        print("\nSafety check errors:")
        for error in errors:
            print(f"  {error}")
        return False

    print(f"\n✓ All playbooks have safety constraints")
    return True


if __name__ == "__main__":
    success = check_safety_constraints()
    sys.exit(0 if success else 1)
