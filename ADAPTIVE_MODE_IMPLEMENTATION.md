# ADAPTIVE Mode Implementation - Complete

**Date:** 2026-02-17
**Version:** 0.2.0 (ADAPTIVE)
**Status:** ✅ Complete

## What Was Implemented

### 1. ADAPTIVE Mixed Mode ("Mode 1.5")

Context-aware assistance level evaluation with automatic clamping:

**Context Parameters:**
- `environment`: prod_client, lab, ctf
- `authorization`: boolean (user assertion)
- `target_owner`: self, client, unknown
- `requested_level`: standard, deep_lab

**Clamping Rules:**
- Default: standard (always safe)
- deep_lab only when: `environment IN {lab, ctf} AND authorized=true AND target_owner=self`
- Reasons provided in every response

**Files Created:**
- `src/bhd_cli/assistant/core/adaptive_mode.py` - Context evaluation logic
- `tests/assistant/test_adaptive_mode.py` - Comprehensive tests

### 2. LLM Provider Routing with Fallback

Multiple provider support with automatic fallback:

**Providers Implemented:**
- **Ollama** (local, CPU): `llama3.2:1b` - no API key needed
- **OpenAI** (cloud): `gpt-4o-mini` - requires `OPENAI_API_KEY`
- **Anthropic** (cloud): `claude-3-5-haiku` - requires `ANTHROPIC_API_KEY`

**Files Created:**
- `src/bhd_cli/assistant/adapters/llm/ollama.py` - Local Ollama provider
- `src/bhd_cli/assistant/adapters/llm/openai_provider.py` - OpenAI provider
- `src/bhd_cli/assistant/adapters/llm/anthropic_provider.py` - Anthropic provider
- `src/bhd_cli/assistant/adapters/llm/router.py` - Router with fallback
- `tests/assistant/test_llm_router.py` - Router tests

### 3. Structured Hypothesis Drafting

LLM-powered hypothesis generation with schema guarantees:

**Pipeline:**
1. Build context-aware prompt (standard vs deep_lab)
2. Call LLM provider with schema
3. Validate JSON against hypothesis.schema.json
4. Repair loop (up to 2 attempts on validation failure)
5. Policy guard check on text fields
6. Return schema-compliant Hypothesis entities

**Files Created:**
- `src/bhd_cli/assistant/core/hypothesis_drafter.py` - Drafting pipeline
- `tests/assistant/test_hypothesis_drafter.py` - Comprehensive tests

### 4. Policy Guard Enhancements

ADAPTIVE mode with reduced false positives:

**Changes:**
- More specific patterns: `"how to exploit step-by-step"` instead of `"how to exploit"`
- Allows normal security testing language
- Still blocks all weaponized content (exploit code, payloads, bypass steps)

**Files Modified:**
- `src/bhd_cli/assistant/policy/guard.py` - Updated patterns
- `tests/assistant/test_policy_guard_adaptive.py` - New ADAPTIVE tests

### 5. CLI Command: hypothesis-draft

New command with full context flags:

```bash
bhd-assist hypothesis-draft \
  --workspace DIR \
  --environment [prod_client|lab|ctf] \
  --authorized \
  --target-owner [self|client|unknown] \
  --assist-level [standard|deep_lab] \
  --provider-order "ollama,openai,anthropic" \
  --max 3
```

**Files Modified:**
- `src/bhd_cli/assistant/cli/main.py` - Added cmd_hypothesis_draft

### 6. Documentation Updates

**Files Updated:**
- `src/bhd_cli/assistant/README.md` - Added ADAPTIVE mode docs, LLM provider setup
- `src/bhd_cli/assistant/IMPLEMENTATION_SUMMARY.md` - Added new features

---

## Implementation Statistics

```
16 files changed, 1571 insertions(+), 65 deletions(-)

New Files Created:
- 6 implementation files (adaptive_mode, hypothesis_drafter, 4 LLM providers)
- 4 test files

Files Modified:
- 2 core files (cli/main.py, policy/guard.py)
- 2 documentation files
- 2 test files
```

**Test Results:**
```
80 passed in 1.08s
100% pass rate
```

---

## How to Run

### Setup (One-Time)

```bash
# Install package
cd ~/BlackHatDefenseLLC/bhd_app
pip install -e .

# Optional: Install cloud provider SDKs
pip install openai anthropic

# Optional: Set up Ollama (local, CPU)
# See: https://ollama.ai
ollama run llama3.2:1b

# Optional: Set API keys for cloud providers
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Basic Workflow

```bash
# 1. Initialize workspace
mkdir pentest-project && cd pentest-project
bhd-assist init --workspace .

# 2. Ingest tool output (e.g., Nmap scan)
bhd-assist ingest --tool nmap --file scan_results.xml --workspace .

# 3. Draft hypotheses (standard mode - safe for production)
bhd-assist hypothesis-draft \
  --workspace . \
  --environment prod_client \
  --target-owner client

# Output shows:
# - effective_assist_level: "standard"
# - reasons: ["requested_level=standard"]
# - provider_used: "ollama" (or whichever succeeded)
# - hypotheses: [...]
```

### Advanced: Deep Lab Mode

```bash
# Deep lab mode (requires ALL conditions)
bhd-assist hypothesis-draft \
  --workspace . \
  --environment lab \
  --authorized \
  --target-owner self \
  --assist-level deep_lab \
  --max 5

# Output shows:
# - effective_assist_level: "deep_lab"
# - reasons: ["deep_lab_enabled: environment=lab/ctf, authorized=true, target_owner=self"]
# - hypotheses: [... with broader guidance ...]
```

### Testing Clamping Behavior

```bash
# Request deep_lab in production → clamped to standard
bhd-assist hypothesis-draft \
  --workspace . \
  --environment prod_client \
  --assist-level deep_lab

# Output shows:
# - effective_assist_level: "standard"
# - reasons: ["clamped: environment=prod_client (requires lab or ctf)"]
```

### Provider Fallback

```bash
# Custom provider order
bhd-assist hypothesis-draft \
  --workspace . \
  --provider-order "openai,anthropic,ollama"

# If OpenAI succeeds:
# - provider_used: "openai"

# If OpenAI fails, tries Anthropic, then Ollama
```

---

## Example Output

### Standard Mode (Production-Safe)

```json
{
  "status": "success",
  "effective_assist_level": "standard",
  "reasons": [
    "requested_level=standard"
  ],
  "provider_used": "ollama",
  "hypotheses": [
    {
      "id": "a7f3c9e2b8d14fa6",
      "related_observations": [
        "b4c3793b7f53e4d4",
        "4030e676c73ebde0"
      ],
      "title": "Exposed Administrative Services Increase Attack Surface",
      "description": "The target system has both RDP (port 3389) and SSH (port 22) services exposed and listening. These administrative interfaces present potential entry points if not properly secured with strong authentication, network controls, and monitoring.",
      "risk_tags": [
        "exposure",
        "remote-admin",
        "authentication",
        "network-security"
      ],
      "confidence": 0.85,
      "rationale": "Based on observations b4c3793b7f53e4d4 (RDP/ms-wbt-server on port 3389) and 4030e676c73ebde0 (OpenSSH on port 22), both administrative services are accessible. This hypothesis warrants validation to confirm: (1) authentication controls are properly configured, (2) services are restricted to authorized networks, (3) monitoring/alerting is in place for access attempts.",
      "requires_validation": true
    }
  ]
}
```

### Deep Lab Mode (Lab Environment)

```json
{
  "status": "success",
  "effective_assist_level": "deep_lab",
  "reasons": [
    "deep_lab_enabled: environment=lab/ctf, authorized=true, target_owner=self"
  ],
  "provider_used": "ollama",
  "hypotheses": [
    {
      "id": "b8e4d1f3c9a25fb7",
      "related_observations": [
        "b4c3793b7f53e4d4"
      ],
      "title": "RDP Service May Accept Weak Authentication Methods",
      "description": "Microsoft Terminal Services 10.0 is exposed on port 3389. In lab testing scenarios, this warrants validation of authentication controls including: password complexity requirements, account lockout policies, MFA enforcement, and network-level authentication (NLA) configuration.",
      "risk_tags": [
        "rdp",
        "authentication-testing",
        "lab-validation",
        "configuration-review"
      ],
      "confidence": 0.75,
      "rationale": "Observation b4c3793b7f53e4d4 shows RDP service listening. For lab environments with proper authorization, recommend testing: (1) default/weak credential rejection, (2) NLA enforcement status, (3) connection logging, (4) session timeout configuration. Focus on validation techniques appropriate for controlled lab testing.",
      "requires_validation": true
    }
  ]
}
```

### Clamped Request

```json
{
  "status": "success",
  "effective_assist_level": "standard",
  "reasons": [
    "clamped: environment=prod_client (requires lab or ctf)"
  ],
  "provider_used": "ollama",
  "hypotheses": [
    "... standard mode hypotheses ..."
  ]
}
```

---

## Safety Guarantees

### What Is BLOCKED (Always)

- ❌ Exploit code generation
- ❌ Payload creation scripts
- ❌ Authentication/authorization bypass steps
- ❌ Persistence mechanism installation
- ❌ Exfiltration method implementation
- ❌ Reverse shell commands
- ❌ Backdoor installation
- ❌ Malware/ransomware
- ❌ DoS/DDoS techniques

### What Is ALLOWED

- ✅ Validation checklists
- ✅ Evidence collection guidance
- ✅ Risk framing and threat modeling
- ✅ Safe verification strategies
- ✅ Testing methodologies (lab mode)
- ✅ Configuration review guidance

### Schema Validation

- ✅ All LLM outputs validated against JSON schema
- ✅ Repair loop (up to 2 attempts) for schema violations
- ✅ Policy guard checks all text fields
- ✅ Blocked content → hypothesis not created

---

## Testing Coverage

**Test Files:**
- `tests/assistant/test_adaptive_mode.py` - Context evaluation (9 tests)
- `tests/assistant/test_hypothesis_drafter.py` - Drafting pipeline (8 tests)
- `tests/assistant/test_llm_router.py` - Provider fallback (4 tests)
- `tests/assistant/test_policy_guard_adaptive.py` - ADAPTIVE patterns (4 tests)

**Coverage:**
- ✅ Effective assist level clamping
- ✅ Schema validation + repair
- ✅ Policy guard blocks weaponized content
- ✅ Provider router fallback
- ✅ CLI integration
- ✅ Observation clustering

**Run Tests:**
```bash
pytest tests/assistant/ -v
# 80 passed in 1.08s
```

---

## Next Steps (Optional Enhancements)

1. **Embedding Support** - Add vector search for observation clustering
2. **More Providers** - Local models (llama.cpp, vLLM)
3. **Prompt Optimization** - Fine-tune prompts per provider
4. **Batch Processing** - Draft multiple hypotheses in parallel
5. **Export Integration** - Auto-export hypotheses to findings

---

## Commit Message

```
feat: Implement ADAPTIVE mode with LLM-powered hypothesis drafting

Add context-aware assistance level system with schema-guaranteed
structured output from multiple LLM providers.

Features:
- ADAPTIVE mode: context evaluation with automatic clamping
  - standard (default): production-safe validation guidance
  - deep_lab: lab/CTF testing methodologies (requires authorization)
- LLM provider routing: Ollama (local) → OpenAI → Anthropic
  - Automatic fallback on failure
  - Schema validation with repair loop (up to 2 attempts)
- Hypothesis drafting: observation → hypothesis pipeline
  - Clustering by category + host
  - Policy guard integration
  - JSON schema compliance guaranteed
- CLI: bhd-assist hypothesis-draft with full context flags
- Policy guard: ADAPTIVE patterns (reduced false positives)

Safety:
- Always blocks weaponized content (exploit code, payloads, bypass steps)
- Allows normal security testing language
- Context-aware clamping ensures production safety

Implementation:
- 16 files changed, 1571 insertions(+), 65 deletions(-)
- 6 new implementation files, 4 new test files
- 80 tests passing (100% pass rate)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

**Delivered by:** Claude Sonnet 4.5
**Implementation Time:** Single session
**Status:** Production-ready for standard mode, lab mode requires Ollama/API keys
