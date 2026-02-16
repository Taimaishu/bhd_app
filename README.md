# bhd-cli

**Security Engagement Documentation Framework for Independent Consultants**

A professional command-line tool for managing penetration testing engagements, tracking findings with validated risk scoring, and generating client-ready reports. Built for security consultants who need reliable documentation workflows without enterprise overhead.

## Features

### Core Capabilities
- ✅ **Engagement Management** - Track multiple client engagements with proper scope and ROE
- ✅ **Finding Management** - Add, edit, delete, search, and filter security findings
- ✅ **Risk Scoring** - Guided impact/likelihood assessment with coaching
- ✅ **Methodology Tracking** - Phase-based pentest methodology with status updates
- ✅ **Validation & Guardrails** - Prevents bad data entry with helpful feedback
- ✅ **Deterministic Output** - Consistent, sorted findings for reliable reporting

### Export & Reporting
- ✅ **Markdown Reports** - Professional reports with executive summaries
- ✅ **JSON Export** - Clean, structured data export for archival or integration
- ✅ **PDF Export** - Client-ready PDF reports (requires reportlab)
- ✅ **Storage Abstraction** - Modular backend design (JSON now, SQLite ready)

### Specialized Tools
- ✅ **Home Audit Wizard** - Quick assessment tool for home networks
- ✅ **Multi-Engagement Support** - Seamlessly switch between client projects
- ✅ **Command-Line First** - Fast, scriptable, no GUI dependencies

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

### Optional: PDF Export Support

To enable PDF export functionality:

```bash
pip install reportlab
# OR install with PDF support
pipx install "git+https://github.com/Taimaishu/bhd_app.git[pdf]"
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

### 4. Generate reports and exports

```bash
# Generate markdown report
bhd-cli report

# Export current engagement to JSON
bhd-cli export json

# Export ALL engagements to JSON
bhd-cli export json --all

# Export current engagement to PDF (requires: pip install reportlab)
bhd-cli export pdf

# Export ALL engagements to PDF
bhd-cli export pdf --all

# Check version
bhd-cli version
```

**Report outputs:**
- `report.md` - Markdown report with executive summary, scope, methodology, and findings
- `export.json` - Clean JSON export with deterministic ordering (meta, scope, methodology, work)
- `report.pdf` - Professional PDF report generated from report.md

**Export modes:**
- Default (no `--all`): Exports only the current engagement
- With `--all`: Exports all engagements in `./engagements` directory (processed in deterministic alphabetical order)

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

### Export & Reporting
```bash
bhd-cli report                        # Generate report.md
bhd-cli export json                   # Export current engagement to JSON
bhd-cli export json --all             # Export all engagements to JSON
bhd-cli export pdf                    # Export current engagement to PDF (requires reportlab)
bhd-cli export pdf --all              # Export all engagements to PDF
bhd-cli version                       # Show version
```

### Other
```bash
bhd-cli add-target <IP>               # Add target to scope
bhd-cli note <text>                   # Add general note
bhd-cli home-audit run                # Run home audit wizard
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

## Changelog

### v1.1.0 (2026-02-15)

**New Features:**
- Added `bhd-cli version` command to display version information
- Added `bhd-cli export json` for clean JSON data export with deterministic ordering
- Added `bhd-cli export pdf` for professional PDF report generation (optional reportlab dependency)
- Implemented storage abstraction layer (`storage.py`) for future SQLite backend support

**Architecture:**
- Refactored data persistence into modular storage layer
- JSON remains current backend; SQLite-ready architecture
- No breaking changes; full backwards compatibility maintained

**Documentation:**
- Updated README with new "Security Engagement Documentation Framework" positioning
- Added export command documentation
- Added optional PDF dependency instructions
- Reorganized feature list by capability area

### v1.0.0 (2026-02-15)

Initial production release with engagement management, finding tracking, risk scoring, methodology tracking, home audit wizard, and markdown report generation.

## Roadmap

### v1.2.0 (Planned)
- SQLite backend option for improved performance and querying
- Finding templates library for common vulnerabilities
- Custom report templates
- Engagement archival and compression

### v1.3.0 (Planned)
- Multi-user support with role-based access
- API endpoints for integration with other tools
- Web UI for report viewing (optional)
- Bulk import/export capabilities

### Future Considerations
- Integration with popular pentest tools (Nmap, Burp, etc.)
- Automated evidence attachment and screenshot management
- Client portal for findings review
- Compliance framework mapping (OWASP, CIS, etc.)

## Requirements

- Python 3.10 or later
- No external dependencies (uses stdlib only)
- Optional: `reportlab>=4.0` for PDF export functionality

## License

MIT License

## Contributing

Contributions welcome! Please ensure:
- Tests pass: `pytest -q`
- Code compiles: `python -m py_compile src/bhd_cli/cli.py`
- Existing commands and behavior preserved
- UX text matches CLI_NAME constant

## Release Process

To create a new release:

```bash
# Tag the release
git tag -a v1.1.0 -m "Release v1.1.0"

# Push with tags
git push origin master --tags
```

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Authors

- Black Hat Defense LLC
- Built with Claude Sonnet 4.5
