# bhd-cli

**Black Hat Defense CLI** - Penetration testing engagement and finding management tool.

A professional CLI for managing penetration testing engagements, tracking findings with risk scoring, and generating client-ready reports.

## Features

- ✅ **Engagement Management** - Track multiple client engagements with proper scope and ROE
- ✅ **Finding Management** - Add, edit, delete, search, and filter security findings
- ✅ **Risk Scoring** - Guided impact/likelihood assessment with coaching
- ✅ **Methodology Tracking** - Phase-based pentest methodology with status updates
- ✅ **Home Audit Wizard** - Quick assessment tool for home networks
- ✅ **Report Generation** - Professional markdown reports with executive summaries
- ✅ **Deterministic Output** - Consistent, sorted findings for reliable reporting
- ✅ **Validation & Guardrails** - Prevents bad data entry with helpful feedback

## Installation

### Option 1: Install from GitHub (recommended)

```bash
pipx install git+https://github.com/Taimaishu/bhd_app.git
```

This installs directly from GitHub without cloning. Use `pipx` for isolated installation or `pip` for system-wide.

### Option 2: Install from local clone with pipx

```bash
git clone https://github.com/Taimaishu/bhd_app.git
cd bhd_app
pipx install .
```

### Option 3: Install from local clone with pip

```bash
git clone https://github.com/Taimaishu/bhd_app.git
cd bhd_app
pip install .
```

### Option 4: Development install (editable)

```bash
git clone https://github.com/Taimaishu/bhd_app.git
cd bhd_app
pip install -e ".[dev]"
```

After installation, `bhd-cli` will be available in your PATH.

## Quick Start

### 1. Create a new engagement

```bash
bhd-cli init
```

You'll be prompted for:
- Client name
- Project name
- Test type (home/web/network/other)
- In-scope targets
- Rules of engagement
- Written authorization (required)

### 2. Add findings

**Option A: Home Audit Wizard (for home networks)**

```bash
bhd-cli home-audit run
```

Interactive questionnaire that auto-generates findings.

**Option B: Manual finding entry**

```bash
bhd-cli finding add
```

Guided process with risk scoring and validation.

### 3. Manage findings

```bash
# List all findings (sorted by ID)
bhd-cli finding list

# Show detailed information
bhd-cli finding show F-001

# Search by keyword
bhd-cli finding search "password"

# Filter by criteria
bhd-cli finding filter --severity High
bhd-cli finding filter --target 192.168.1.1
bhd-cli finding filter --status open

# Edit finding
bhd-cli finding edit F-001

# Update status
bhd-cli finding status F-001 remediated

# Delete finding
bhd-cli finding delete F-001
```

### 4. Generate report

```bash
bhd-cli report
```

Creates `report.md` in the engagement folder with:
- Executive summary
- Scope and ROE
- Methodology phases
- Findings summary table (sorted by ID)
- Detailed findings with evidence and recommendations

### 5. Manage multiple engagements

```bash
# List all engagements
bhd-cli engagements list

# Switch to different engagement
bhd-cli engagements switch <engagement-name>

# Show current engagement
bhd-cli show
```

## Data Storage

bhd-cli stores engagement data in JSON format in an `engagements/` directory:

```
engagements/
├── .current                                    # Current engagement pointer
├── client-project-20260215-123456/
│   ├── engagement.json                        # All engagement data
│   └── report.md                              # Generated report
```

**Location behavior:**
- When run from the project directory: creates `engagements/` in the project
- When installed and run from anywhere: creates `engagements/` in current directory
- The `.current` file tracks which engagement is active

**Tip:** Run bhd-cli from a dedicated pentest workspace directory to keep all engagement data organized in one place.

## Command Reference

### Engagements
```bash
bhd-cli engagements list              # List all engagements
bhd-cli engagements switch <name>     # Switch to engagement
bhd-cli init                          # Create new engagement
bhd-cli show                          # Show current engagement
```

### Findings (8 commands)
```bash
bhd-cli finding add                   # Add new finding
bhd-cli finding list                  # List all findings
bhd-cli finding show <ID>             # Show detailed finding
bhd-cli finding edit <ID>             # Edit finding
bhd-cli finding delete <ID>           # Delete finding
bhd-cli finding status <ID> <status>  # Update status
bhd-cli finding filter [options]      # Filter findings
bhd-cli finding search <keyword>      # Search findings
```

**Status values:** `open` | `remediated` | `accepted` | `retest`

### Phases
```bash
bhd-cli phase status                  # Show all phases
bhd-cli phase set <phase> <status>    # Update phase
bhd-cli phase note <phase> <text>     # Add phase note
```

**Phase names:** Pre-Engagement, Reconnaissance, Scanning, Enumeration, Vulnerability Analysis, Exploitation, Reporting

### Other
```bash
bhd-cli add-target <IP>               # Add target to scope
bhd-cli note <text>                   # Add general note
bhd-cli home-audit run                # Run home audit wizard
bhd-cli report                        # Generate report
```

## Development

### Setup

```bash
git clone https://github.com/Taimaishu/bhd_app.git
cd bhd_app
pip install -e ".[dev]"
```

### Running tests

```bash
pytest -q
```

### Project structure

```
bhd_app/
├── src/
│   └── bhd_cli/
│       ├── __init__.py
│       ├── __main__.py        # python -m bhd_cli
│       └── cli.py             # Main CLI code
├── tests/
│   └── test_smoke.py          # Smoke tests
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI
├── pyproject.toml             # Package configuration
├── README.md
├── bhd.py                     # Backwards compatibility stub
└── bhd-cli                    # Wrapper script (development)
```

### Backwards compatibility

The top-level `bhd.py` is a stub that imports and calls the package. Existing references to `python3 bhd.py` will still work.

## Examples

### Home network assessment

```bash
# Create engagement
bhd-cli init
# Client: HomeOwner, Project: Home Security Audit, Type: home

# Run home audit wizard
bhd-cli home-audit run
# Answer questions about router, WiFi, devices

# Review findings
bhd-cli finding list
bhd-cli finding filter --severity Medium

# Generate report
bhd-cli report
```

### Multi-client workflow

```bash
# Morning - Client A
bhd-cli engagements list
bhd-cli engagements switch clienta-pentest-20260215-090000
bhd-cli finding filter --status open
bhd-cli finding add

# Afternoon - Client B
bhd-cli engagements switch clientb-webapp-20260215-140000
bhd-cli finding list
bhd-cli report
```

## Requirements

- Python 3.10 or later
- No external dependencies (uses stdlib only)

## License

MIT License

## Contributing

Contributions welcome! Please ensure:
- Tests pass: `pytest -q`
- Code compiles: `python -m py_compile src/bhd_cli/cli.py`
- Existing commands and behavior preserved
- UX text matches CLI_NAME constant

## Authors

- Black Hat Defense LLC
- Built with Claude Sonnet 4.5
