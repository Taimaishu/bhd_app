# Security Statement

## What bhd-assist Is

**bhd-assist is NOT a penetration testing tool.**

bhd-assist is a **documentation-centric assistance framework** designed to support security professionals in:

- Organizing and tracking security assessment workflows
- Validating potential security findings through safe, evidence-based verification
- Documenting observations and evidence in a structured format
- Generating finding drafts compatible with bhd-cli
- Providing phase-driven guidance aligned with assessment methodologies

## What bhd-assist Does NOT Do

bhd-assist explicitly **DOES NOT**:

- ❌ Generate exploit code or payloads
- ❌ Provide step-by-step exploitation instructions
- ❌ Automate attacks or vulnerability exploitation
- ❌ Generate bypass techniques for security controls
- ❌ Provide persistence mechanisms or backdoors
- ❌ Generate credential cracking or brute-force scripts
- ❌ Create weaponized tools or attack automation
- ❌ Provide privilege escalation techniques
- ❌ Generate data exfiltration methods
- ❌ Provide DoS/DDoS attack guidance

## Design Principles

### 1. Legal and Authorized Use Only

All functionality assumes:
- Written authorization for security testing
- Compliance with applicable laws and regulations
- Adherence to rules of engagement
- Coordination with system owners

### 2. Validation-First Approach

The framework focuses on **safe verification** of potential security issues:
- READ-ONLY operations where possible
- Test account usage (never production accounts)
- Evidence collection, not exploitation
- Documentation of observations, not weaponization

### 3. Policy-Enforced Guardrails

All LLM outputs pass through a policy guard that:
- Blocks disallowed content patterns
- Enforces JSON schema constraints
- Logs all decisions to an append-only audit trail
- Redacts sensitive information

### 4. Transparency and Audit Trail

- All decisions logged to `decision_log.jsonl`
- Policy violations are recorded and blocked
- Evidence of safe operation practices
- Full traceability of all actions

## Assistance Levels

### Level 0 (VALIDATION_ONLY) - Default Production Mode

**This is the default and recommended mode for all production use.**

Characteristics:
- Evidence collection and documentation only
- Safe verification playbooks (no exploitation)
- READ-ONLY operations preferred
- Strict policy enforcement
- No exploitation guidance whatsoever

### Level 1 (LAB_TRAINING) - Lab/Training Mode

**Requires explicit profile file.**

Characteristics:
- Broader guidance for learning environments
- Still NO exploit code generation
- Still NO weaponized automation
- Requires explicit `profile.json` with `assistance_level: 1`
- Intended for controlled lab environments only

### Level 2

**Not implemented. Reserved for future use.**

## Responsible Use

### Users Must

✅ Obtain written authorization before testing
✅ Comply with all applicable laws and regulations
✅ Follow rules of engagement
✅ Document all activities
✅ Report findings responsibly
✅ Protect sensitive information
✅ Use test accounts (not production users)
✅ Coordinate with system owners

### Users Must NOT

❌ Use bhd-assist for unauthorized testing
❌ Attempt to bypass policy guardrails
❌ Use findings for malicious purposes
❌ Violate laws or regulations
❌ Test systems without permission
❌ Cause harm or disruption
❌ Ignore safety constraints in playbooks

## Reporting Security Issues

If you discover a security issue with bhd-assist itself:

1. **DO NOT** disclose publicly
2. Email security concerns to: [maintainer contact]
3. Include:
   - Description of the issue
   - Steps to reproduce
   - Potential impact
   - Suggested remediation (if any)

We will respond within 48 hours and work to address confirmed issues promptly.

## Compliance

bhd-assist is designed to support compliance with:

- Computer Fraud and Abuse Act (CFAA)
- GDPR data protection requirements
- SOC 2 audit evidence requirements
- PCI DSS penetration testing documentation
- HIPAA security assessment documentation
- NERC CIP (for ICS/SCADA assessments)
- IEC 62443 (for OT security)

**Note:** Users are responsible for ensuring their own compliance. bhd-assist provides tools to support compliance but does not guarantee it.

## License and Disclaimer

bhd-assist is provided "as is" without warranty of any kind. Users are solely responsible for their use of this software in compliance with all applicable laws and regulations.

The maintainers of bhd-assist disclaim all liability for any unauthorized, illegal, or harmful use of this software.

---

**Last Updated:** 2026-02-17
**Version:** 0.1.0
