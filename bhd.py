#!/usr/bin/env python3
"""
Backwards compatibility stub for bhd.py.
The actual CLI is now in src/bhd_cli/cli.py.
This stub allows existing references to work.
"""
import sys
from pathlib import Path

# Add src to path for development use
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from bhd_cli.cli import main
    main()
except ImportError as e:
    print(f"Error: Could not import bhd_cli package.", file=sys.stderr)
    print(f"Please install: pip install -e .", file=sys.stderr)
    print(f"Details: {e}", file=sys.stderr)
    sys.exit(1)
