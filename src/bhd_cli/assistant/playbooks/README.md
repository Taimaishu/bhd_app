# Playbook System

## Overview

Playbooks are YAML files that define **validation-focused** security testing procedures. They provide:

- Step-by-step validation guidance (NOT exploitation)
- Evidence collection requirements
- Safety constraints (DO NOT rules)
- Finding templates for documentation

**Playbooks do NOT contain exploit code or weaponized automation.**

---

## Playbook Format

### Required Fields

```yaml
id: unique_playbook_identifier
version: 1.0.0  # Semantic versioning
name: Human-Readable Playbook Name
type: validation | evidence_collection | verification
test_types:
  - web
  - network
  - ics

description: |
  Detailed description of what this playbook validates

steps:
  - step_number: 1
    action: What to do
    description: How to do it safely
    expected_outcome: What you should observe
    tools: [BurpSuite, curl]

evidence_objects:
  - id: evidence_item_1
    type: request_response_pair
    description: What evidence to collect
    required: true

finding_template:
  title: Title for finding
  description: Technical description
  impact_level: High
  likelihood: Medium
  remediation: How to fix
  business_impact: Why it matters

safety_constraints:
  - DO NOT perform unauthorized actions
  - DO NOT access production data
  - DO NOT cause service disruption
```

### Valid Evidence Types

From `evidence.schema.json`:

- `request_response_pair` - HTTP requests and responses
- `screenshot` - Visual evidence
- `configuration_snapshot` - Config files/settings
- `banner_capture` - Service banners/version info
- `network_trace` - Packet captures
- `log_entry` - Log file entries
- `metadata` - Timestamps, environment info
- `other` - Other evidence types

### Valid Test Types

- `web` - Web application testing
- `network` - Network security testing
- `home` - Home network audits
- `ics` - Industrial control systems
- `scada` - SCADA systems
- `ot` - Operational technology
- `osint` - OSINT and attack surface analysis
- `other` - Other test types

### Valid Impact Levels

From `finding_draft.schema.json`:

- `low`
- `medium`
- `high`
- `critical`

### Valid Likelihood Levels

- `low`
- `medium`
- `high`
- `very_high`

---

## Safety Constraints

**Every playbook MUST include safety constraints.**

Required minimum: **3 safety constraints**

Examples:
- `DO NOT attempt authentication with default credentials`
- `DO NOT modify production data`
- `DO NOT scan outside authorized scope`
- `DO NOT test during production hours without approval`
- `STOP immediately if unintended access occurs`

---

## Adding a New Playbook

### Step 1: Create YAML File

Create file in `library/` directory:

```bash
cd src/bhd_cli/assistant/playbooks/library/
touch my_new_playbook.yaml
```

### Step 2: Define Playbook Structure

Use existing playbooks as templates. Minimum structure:

```yaml
id: my_new_playbook
version: 1.0.0
name: My New Validation Playbook
type: validation
test_types:
  - web

description: What this playbook validates

steps:
  - step_number: 1
    action: First validation step
    description: How to perform this step
    expected_outcome: What should happen

evidence_objects:
  - id: evidence_1
    type: request_response_pair
    description: Evidence to collect
    required: true

finding_template:
  title: Finding title
  description: Technical description
  impact_level: medium
  likelihood: medium
  remediation: How to fix
  business_impact: Business context

safety_constraints:
  - DO NOT perform unauthorized testing
  - DO NOT access production accounts
  - STOP if unexpected behavior occurs
```

### Step 3: Validate Schema

```bash
python scripts/validate_schemas.py
```

### Step 4: Check Safety Constraints

```bash
python scripts/check_playbook_safety.py
```

### Step 5: Test Rendering

```bash
bhd-assist playbook-render my_new_playbook
bhd-assist playbook-render my_new_playbook --format evidence
```

### Step 6: Add Selector Rules (Optional)

If playbook should be auto-selected, add rules to `selectors/selector_rules.yaml`:

```yaml
rules:
  - id: my_rule_id
    test_types: [web]
    conditions:
      - observation_type: http_response
        data_contains:
          - key: status_code
            value: 200
    playbook_id: my_new_playbook
    priority: 90
```

---

## Best Practices

### DO

✅ Focus on safe verification steps
✅ Provide clear expected outcomes
✅ Include comprehensive safety constraints
✅ Document evidence requirements clearly
✅ Use tool-agnostic language where possible
✅ Include references to standards (OWASP, NIST, etc.)

### DON'T

❌ Include exploit code or payloads
❌ Provide step-by-step exploitation instructions
❌ Include weaponized automation
❌ Skip safety constraints
❌ Assume user has malicious intent
❌ Encourage unauthorized access

---

## Validation Checklist

Before submitting a new playbook:

- [ ] Schema validation passes
- [ ] Safety check passes
- [ ] Minimum 3 safety constraints
- [ ] All required fields present
- [ ] Version follows semver (X.Y.Z)
- [ ] Evidence types are valid enums
- [ ] Impact/likelihood are valid enums
- [ ] Test types are valid enums
- [ ] Renders correctly as checklist
- [ ] Renders correctly as evidence plan
- [ ] No exploitation guidance
- [ ] Clear authorization requirements
- [ ] References included (if applicable)

---

## Playbook Lifecycle

### Version Updates

Follow semantic versioning:

- **Major (X.0.0)**: Breaking changes to playbook structure
- **Minor (0.X.0)**: New steps, evidence, or significant changes
- **Patch (0.0.X)**: Typos, clarifications, minor improvements

### Deprecation

To deprecate a playbook:

1. Add `deprecated: true` field
2. Add `deprecated_reason` field
3. Add `replacement_playbook_id` if applicable
4. Keep file for backwards compatibility

### Review Schedule

Playbooks should be reviewed:

- Annually for accuracy
- When standards update (OWASP, NIST, etc.)
- When tools change significantly
- When new vulnerabilities emerge

---

## Example Playbooks

### Web Application

- `idor_validation.yaml` - IDOR testing
- `authz_broken_access.yaml` - Access control testing

### Network

- `exposed_admin_interfaces.yaml` - Admin service exposure

### ICS/SCADA/OT

- `modbus_exposure.yaml` - Modbus TCP validation
- `opcua_exposure.yaml` - OPC UA security testing

---

## Troubleshooting

### Schema Validation Fails

```bash
# Check for syntax errors
python -c "import yaml; yaml.safe_load(open('library/my_playbook.yaml'))"

# Validate against schema
python scripts/validate_schemas.py
```

### Playbook Not Found

- Check file is in `library/` directory
- Check filename matches playbook `id` field
- Check file extension is `.yaml` (not `.yml`)

### Selector Not Triggering

- Verify selector rules in `selectors/selector_rules.yaml`
- Check observation category matches
- Check test_type matches
- Verify priority is not too low

---

## Contributing

See main [CONTRIBUTING.md](../../../CONTRIBUTING.md) for:

- Code of conduct
- Pull request process
- Review criteria
- Style guidelines

---

**Last Updated:** 2026-02-17
**Schema Version:** 1.0
