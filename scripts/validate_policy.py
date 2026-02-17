#!/usr/bin/env python3
"""Validate policy guard patterns."""
import re
import sys
from pathlib import Path


def validate_policy_patterns():
    """Validate policy guard patterns are valid regex."""
    base_dir = Path(__file__).parent.parent
    guard_file = base_dir / "src" / "bhd_cli" / "assistant" / "policy" / "guard.py"

    if not guard_file.exists():
        print(f"Policy guard file not found: {guard_file}")
        return False

    with open(guard_file) as f:
        content = f.read()

    # Extract pattern lists
    errors = []

    # Find ALWAYS_BLOCKED_PATTERNS
    always_match = re.search(r'ALWAYS_BLOCKED_PATTERNS = \[(.*?)\]', content, re.DOTALL)
    if always_match:
        patterns_text = always_match.group(1)
        patterns = re.findall(r'r"([^"]+)"', patterns_text)

        print(f"Checking {len(patterns)} always-blocked patterns...")
        for pattern in patterns:
            try:
                re.compile(pattern, re.IGNORECASE)
                print(f"  ✓ {pattern[:50]}")
            except re.error as e:
                errors.append(f"✗ Invalid regex: {pattern}: {e}")

    # Find VALIDATION_ONLY_BLOCKED_PATTERNS
    level0_match = re.search(r'VALIDATION_ONLY_BLOCKED_PATTERNS = \[(.*?)\]', content, re.DOTALL)
    if level0_match:
        patterns_text = level0_match.group(1)
        patterns = re.findall(r'r"([^"]+)"', patterns_text)

        print(f"\nChecking {len(patterns)} validation-only patterns...")
        for pattern in patterns:
            try:
                re.compile(pattern, re.IGNORECASE)
                print(f"  ✓ {pattern[:50]}")
            except re.error as e:
                errors.append(f"✗ Invalid regex: {pattern}: {e}")

    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  {error}")
        return False

    print("\n✓ All policy patterns valid")
    return True


if __name__ == "__main__":
    success = validate_policy_patterns()
    sys.exit(0 if success else 1)
