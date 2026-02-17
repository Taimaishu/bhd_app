# Assistance Levels Policy

## Overview

bhd-assist operates under a tiered assistance level system that controls what guidance and outputs are provided. This policy ensures safe, legal, and authorized use of the framework.

## Assistance Levels

### Level 0: VALIDATION_ONLY (Default)

**Status:** Production-ready, default mode
**Activation:** Automatically enabled, no configuration required

#### Allowed Operations

✅ Evidence collection playbooks
✅ Safe verification steps (READ-ONLY preferred)
✅ Documentation and note-taking
✅ Finding draft generation
✅ Tool output ingestion and normalization
✅ Playbook rendering (checklists, evidence plans)
✅ Export to bhd-cli format

#### Blocked Operations

❌ Exploit code generation
❌ Step-by-step exploitation instructions
❌ Attack vector implementation guidance
❌ Payload generation
❌ Bypass technique development
❌ Persistence mechanism suggestions
❌ Privilege escalation playbooks
❌ Data exfiltration methods
❌ Weaponized automation
❌ Any write operations without explicit safety review

#### Use Cases

- Production security assessments
- Compliance audits
- Customer-facing penetration tests
- Internal security reviews
- Vulnerability validation
- Evidence documentation

#### Policy Enforcement

All content passes through policy guard checking:
- Blocked pattern list (always enforced)
- Validation-only blocked patterns (Level 0 specific)
- JSON schema validation
- Decision logging to `decision_log.jsonl`

---

### Level 1: LAB_TRAINING

**Status:** Experimental, requires explicit opt-in
**Activation:** Requires profile file with `assistance_level: 1`

#### Opt-In Requirements

To enable Level 1, create a `profile.json` file:

```json
{
  "assistance_level": 1,
  "environment": "lab",
  "purpose": "training",
  "authorized_by": "Lab Administrator",
  "date": "2026-02-17"
}
```

Pass to bhd-assist with:
```bash
bhd-assist init --profile profile.json
```

#### Additional Capabilities (vs Level 0)

✅ Broader guidance on vulnerability mechanics
✅ Educational context on attack techniques
✅ Reference to exploitation concepts (theoretical)
✅ Lab-specific testing scenarios

#### Still Blocked

❌ Exploit code generation (still blocked)
❌ Weaponized payloads (still blocked)
❌ Bypass automation (still blocked)
❌ Malicious tool creation (still blocked)

#### Use Cases

- Security training environments
- Capture-the-Flag (CTF) competitions
- Educational labs
- Controlled research environments
- Internal skill development

#### Safety Requirements

- Must be used in isolated lab networks
- No production systems
- Requires authorization documentation
- All activities logged
- Subject to same audit trail requirements

---

### Level 2: RESERVED

**Status:** Not implemented
**Purpose:** Reserved for future advanced capabilities

---

## Decision Log and Audit Trail

### Purpose

All assistance decisions are logged to provide:
- Transparency in operations
- Audit trail for compliance
- Debugging and quality assurance
- Policy violation detection

### Log Format

Append-only JSONL file: `decision_log.jsonl`

Each entry contains:
```json
{
  "timestamp": "2026-02-17T12:00:00.000000Z",
  "event_type": "playbook_selected|policy_blocked|finding_drafted",
  "assistance_level": "VALIDATION_ONLY",
  "details": {
    "reason": "...",
    "context": "..."
  },
  "redacted": false
}
```

### Event Types

- `playbook_selected` - Playbook chosen for user
- `playbook_rendered` - Playbook rendered as checklist/evidence plan
- `policy_blocked` - Content rejected by policy guard
- `finding_drafted` - Finding draft created
- `observation_ingested` - Tool output parsed
- `export_completed` - Export to bhd-cli format

### Redaction

Sensitive information is automatically redacted:
- Secrets and credentials
- Personal identifiable information (PII)
- Target system details (when flagged)
- Policy violation details (sanitized)

Redacted entries show:
```json
{
  "details": {
    "reason": "policy_blocked",
    "pattern": "[REDACTED]",
    "context": "[REDACTED]"
  },
  "redacted": true
}
```

### Log Retention

Decision logs should be:
- Retained for audit purposes (minimum 1 year recommended)
- Backed up securely
- Protected from unauthorized access
- Included in engagement documentation
- Available for compliance reviews

### Access Control

Decision logs contain sensitive operational data:
- Restrict access to authorized personnel only
- Do not share logs outside the organization
- Sanitize logs before external sharing
- Treat as confidential assessment data

---

## Policy Guard Implementation

### Always-Blocked Patterns

Regardless of assistance level:

```
- exploit code
- payload generation
- bypass (authentication|authorization)
- persistence mechanism
- privilege escalation step
- exfiltration method
- weaponized (script|tool|payload)
- reverse shell
- backdoor
- malware
- ransomware
- denial of service
- dos attack
- ddos
```

### Level 0 Additional Blocks

```
- how to exploit
- execution step.*exploit
- attack vector.*implement
- injection payload
```

### Enforcement

1. Content → Policy Guard
2. Pattern matching (regex, case-insensitive)
3. If match → BLOCK + LOG
4. If no match → Allow + LOG

---

## Schema Validation

All structured outputs must conform to JSON schemas:

- **Playbooks:** `playbook.schema.json`
- **Evidence Plans:** `evidence.schema.json`
- **Finding Drafts:** Validated against bhd-cli format

Schema violations are:
- Logged as errors
- Rejected before output
- Never silently ignored

---

## Compliance and Audit

### Audit Questions Answered

✅ What assistance level was used?
✅ What playbooks were executed?
✅ Were any policy violations attempted?
✅ What findings were generated?
✅ What evidence was collected?
✅ Were all operations logged?

### Compliance Support

The policy framework supports:

- **SOC 2 Type II:** Audit trail, access controls, policy enforcement
- **ISO 27001:** Security controls, risk management, incident logging
- **PCI DSS:** Penetration testing documentation, evidence retention
- **HIPAA:** Security assessment documentation, audit logs
- **GDPR:** Data minimization, purpose limitation, audit requirements

---

## Updating This Policy

Policy changes require:
1. Version bump in policy document
2. Update to `CHANGELOG.md`
3. Communication to all users
4. Review of blocked pattern lists
5. Schema updates (if applicable)

**Current Policy Version:** 1.0.0
**Last Updated:** 2026-02-17
**Next Review Date:** 2026-08-17
