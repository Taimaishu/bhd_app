# bhd-assist: AI-Powered Penetration Testing Assistant

**Version:** 0.1.0
**Status:** MVP/Alpha

## Overview

bhd-assist is a **documentation-centric assistance framework** (NOT a penetration testing tool) designed to support security professionals in organizing, validating, and documenting security assessment activities.

### What It Is

- Documentation and workflow assistance
- Evidence collection guidance
- Safe validation playbooks
- Finding draft generator
- bhd-cli integration layer

### What It Is NOT

- ❌ NOT an exploitation tool
- ❌ NOT an automated attack framework
- ❌ NOT a vulnerability scanner
- ❌ Does NOT generate exploit code
- ❌ Does NOT provide weaponized automation

See [SECURITY.md](./SECURITY.md) for full security statement.

---

## Architecture

bhd-assist follows **hexagonal/ports-and-adapters architecture**:

```
┌─────────────────────────────────────────────────────┐
│                    CLI Layer                        │
│              (bhd-assist commands)                  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│                  Core Domain                        │
│  ┌──────────────┐  ┌───────────────┐               │
│  │   Entities   │  │  Use Cases    │               │
│  │  - Playbook  │  │  - Select PB  │               │
│  │  - Evidence  │  │  - Render PB  │               │
│  │  - Finding   │  │  - Export     │               │
│  └──────────────┘  └───────────────┘               │
│                       │                             │
│  ┌────────────────────┴───────────────────┐        │
│  │         Ports (Interfaces)             │        │
│  │  - IStoragePort                        │        │
│  │  - ILLMPort                            │        │
│  │  - IParserPort                         │        │
│  │  - IPolicyGuard                        │        │
│  └────────────────────────────────────────┘        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│                 Adapters                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Storage  │  │   LLM    │  │ Parsers  │         │
│  │  (JSON)  │  │  (Mock)  │  │  (Nmap)  │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│              External Systems                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ bhd-cli  │  │   LLM    │  │  Files   │         │
│  │ Export   │  │ Provider │  │  JSONL   │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
src/bhd_cli/assistant/
├── __init__.py
├── __main__.py              # Legacy entry point: python -m bhd_cli.assistant (use bhd-assist CLI instead)
├── README.md                # This file
├── SECURITY.md              # Security statement
├── POLICY.md                # Assistance levels policy
│
├── core/                    # Domain logic
│   ├── entities.py          # Core entities (Observation, EvidencePlan, FindingDraft)
│   └── ports.py             # Interfaces for adapters
│
├── policy/                  # Policy enforcement
│   └── guard.py             # PolicyGuard with assistance levels
│
├── playbooks/               # Playbook system
│   ├── loader.py            # PlaybookLoader
│   ├── selector.py          # PlaybookSelector
│   ├── schemas/             # JSON schemas
│   │   ├── playbook.schema.json
│   │   └── evidence.schema.json
│   ├── selectors/
│   │   └── selector_rules.yaml
│   └── library/             # Validation playbooks
│       ├── idor_validation.yaml
│       ├── authz_broken_access.yaml
│       ├── exposed_admin_interfaces.yaml
│       ├── modbus_exposure.yaml
│       └── opcua_exposure.yaml
│
├── adapters/                # External system adapters
│   ├── storage/
│   │   └── json_store.py    # JSONStorageAdapter
│   ├── llm/
│   │   └── mock_provider.py # MockLLMProvider
│   └── parsers/
│       └── nmap_parser.py   # NmapParser (stub)
│
├── integration/             # Integration layers
│   └── bhd_cli/
│       └── exporter.py      # BHDCLIExporter
│
└── cli/                     # CLI commands
    └── main.py              # argparse commands
```

---

## Quick Start

### Installation

```bash
cd ~/BlackHatDefenseLLC/bhd_app
pip install -e .
```

### Initialize Workspace

```bash
bhd-assist init
```

This creates `.bhd-assist/config.json` with default Level 0 (VALIDATION_ONLY).

### List Available Playbooks

```bash
bhd-assist playbook-list
bhd-assist playbook-list --test-type web
```

### Render a Playbook

```bash
# Render as human-readable checklist
bhd-assist playbook-render idor_validation

# Render as evidence plan JSON
bhd-assist playbook-render idor_validation --format evidence

# Render as finding draft skeleton
bhd-assist playbook-render idor_validation --format finding --asset "webapp.example.com"
```

### Ingest Tool Output

```bash
bhd-assist ingest --tool nmap --file scan_results.xml --workspace .
```

### Suggest Playbooks

```bash
bhd-assist suggest-playbooks --test-type network --workspace . --explain
```

### Export to bhd-cli (Stub)

```bash
bhd-assist export --output findings_export.json
```

---

## Playbook System

### Playbook Format

Playbooks are YAML files validated against `playbook.schema.json`.

Required fields:
- `id`: Unique identifier
- `version`: Semantic version (X.Y.Z)
- `name`: Human-readable name
- `type`: validation | evidence_collection | verification
- `test_types`: Array of applicable test types
- `steps`: Array of validation steps
- `evidence_objects`: Array of evidence to collect
- `finding_template`: Template for finding generation
- `safety_constraints`: Array of DO NOT rules

See [playbooks/README.md](./playbooks/README.md) for detailed format specification.

### Selector Rules

Playbooks are automatically selected based on:
- Test type (web, network, ics, etc.)
- Normalized observations (port scans, HTTP responses, etc.)
- Priority scores

Rules defined in `playbooks/selectors/selector_rules.yaml`.

---

## Integration with bhd-cli

bhd-assist generates finding drafts compatible with bhd-cli:

```python
from bhd_cli.assistant.integration.bhd_cli.exporter import BHDCLIExporter

# Export finding drafts
BHDCLIExporter.export_json(drafts, "findings.json")

# Import into bhd-cli
# (Manual step: review findings.json and import into bhd-cli)
```

Finding draft format maps to bhd-cli fields:
- `title` → `title`
- `description` → `description`
- `affected_asset` → `affected_target`
- `evidence_refs` → `evidence`
- `impact_level` → `impact_level`
- `likelihood` → `likelihood`
- `remediation` → `remediation`
- `business_impact` → `business_impact`

---

## Assistance Levels

### Level 0: VALIDATION_ONLY (Default)

✅ Safe verification playbooks
✅ Evidence collection guidance
✅ Finding draft generation
❌ NO exploitation guidance
❌ NO weaponized automation

**Default for all production use.**

### Level 1: LAB_TRAINING

Requires explicit opt-in via `profile.json`:

```json
{
  "assistance_level": 1,
  "environment": "lab",
  "purpose": "training"
}
```

✅ Broader educational guidance
❌ Still NO exploit code generation
❌ Still NO weaponized tools

See [POLICY.md](./POLICY.md) for complete policy specification.

---

## Decision Logging

All decisions logged to `decision_log.jsonl` (append-only):

```json
{
  "timestamp": "2026-02-17T12:00:00Z",
  "event_type": "playbook_selected",
  "assistance_level": "VALIDATION_ONLY",
  "details": {...},
  "redacted": false
}
```

Provides audit trail for:
- Policy compliance
- Debugging
- Quality assurance
- Incident response

---

## Development

### Running Tests

```bash
cd ~/BlackHatDefenseLLC/bhd_app
pytest tests/assistant/ -v
```

### Testing CLI Entry Point

```bash
bhd-assist --help
bhd-assist playbook-list
```

### Schema Validation

```bash
python scripts/validate_schemas.py
```

### Safety Checks

```bash
python scripts/check_playbook_safety.py
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Adding New Playbooks

See [playbooks/README.md](./playbooks/README.md) for detailed instructions.

Quick summary:
1. Create YAML file in `playbooks/library/`
2. Follow schema format
3. Include safety_constraints (minimum 3)
4. Add selector rules if needed
5. Validate: `python scripts/validate_schemas.py`
6. Test: `bhd-assist playbook-render <playbook_id>`

---

## Roadmap

### MVP Complete (v0.1.0)
- ✅ Core architecture
- ✅ Policy guard system
- ✅ Playbook system
- ✅ 5 starter playbooks
- ✅ CLI commands (stubs)
- ✅ bhd-cli integration

### Next Steps (v0.2.0)
- [ ] Real LLM provider integration
- [ ] Tool output parsers (nmap, Burp Suite, etc.)
- [ ] Observation ingestion pipeline
- [ ] Playbook selection automation
- [ ] Evidence tracking
- [ ] Session management

### Future (v0.3.0+)
- [ ] Web UI for playbook rendering
- [ ] Report generation
- [ ] Multi-engagement support
- [ ] Plugin system
- [ ] Advanced LLM prompting

---

## Contributing

1. All contributions must maintain policy guardrails
2. New playbooks must pass schema validation
3. Safety constraints are mandatory
4. Document assistance level requirements
5. Include tests for new features

---

## License

See main project LICENSE file.

---

## Support

For issues, questions, or feature requests:
- GitHub Issues: [repository URL]
- Documentation: This README and linked files
- Security Issues: See [SECURITY.md](./SECURITY.md)

---

**Last Updated:** 2026-02-17
**Version:** 0.1.0
**Status:** MVP/Alpha
