# BHD Assistant - Complete Usage Guide

Everything we built today in one place!

---

## Quick Reference

### Main CLIs
- `bhd-cli` - Engagement management
- `bhd-assist` - AI-powered assistant (NEW features today)

### New Commands Added Today
- `bhd-assist hypothesis-draft` - LLM-powered hypothesis generation with ADAPTIVE mode

---

## Setup (One-Time)

### 1. Install Package
```bash
cd ~/BlackHatDefenseLLC/bhd_app
pip install -e .
```

### 2. Verify Installation
```bash
bhd-cli --help          # Main CLI
bhd-assist --help       # Assistant CLI (should show "hypothesis-draft")
```

### 3. API Keys (Already Configured!)
Your API keys are in:
- `~/.bashrc` - Auto-loaded in new terminals
- `.env` file - Project-specific loading
- `load_keys.sh` - Helper script

**Verify keys are loaded:**
```bash
echo $OPENAI_API_KEY | cut -c1-20
echo $ANTHROPIC_API_KEY | cut -c1-25
```

If not showing, load them:
```bash
source ~/.bashrc
# OR
cd ~/BlackHatDefenseLLC/bhd_app && source load_keys.sh
```

---

## Complete Workflow

### Basic Workflow (Production-Safe)

```bash
# 1. Create project workspace
mkdir ~/pentests/client-project
cd ~/pentests/client-project

# 2. Initialize bhd-assist workspace
bhd-assist init --workspace .

# 3. Run your tools (e.g., Nmap)
nmap -sV -p- 192.168.1.100 -oX scan_results.xml

# 4. Ingest tool output
bhd-assist ingest \
  --tool nmap \
  --file scan_results.xml \
  --workspace .

# 5. Get playbook suggestions
bhd-assist suggest-playbooks \
  --test-type network \
  --workspace . \
  --explain

# 6. Draft hypotheses (NEW! - standard mode = always safe)
bhd-assist hypothesis-draft \
  --workspace . \
  --environment prod_client \
  --target-owner client

# Output will be JSON with:
# - effective_assist_level: "standard"
# - hypotheses: [...]
# - provider_used: "ollama" or "openai" or "anthropic"

# 7. View playbook for validation
bhd-assist playbook-render exposed_admin_interfaces

# 8. Create engagement in bhd-cli
cd ..
bhd-cli init
# Follow prompts...

# 9. Add findings manually based on hypotheses and playbook validation
bhd-cli finding add
# Follow prompts...

# 10. Generate report
bhd-cli report
```

---

## ADAPTIVE Mode Usage (NEW!)

### Context Flags Explained

**--environment** (Where are you?)
- `prod_client` - Client production systems (default, safest)
- `lab` - Your own lab environment
- `ctf` - CTF competition

**--authorized** (Do you have written authorization?)
- Include this flag if you have written authorization
- Omit if you don't

**--target-owner** (Who owns the target?)
- `client` - Client-owned systems (default)
- `self` - Your own systems
- `unknown` - Unknown ownership

**--assist-level** (What level of guidance?)
- `standard` - Validation/evidence only (default, always safe)
- `deep_lab` - Broader testing methodologies (requires lab+auth+self)

### Example Scenarios

#### Scenario 1: Client Production Assessment (Standard Mode)
```bash
bhd-assist hypothesis-draft \
  --workspace . \
  --environment prod_client \
  --target-owner client \
  --assist-level standard

# Result: effective_assist_level="standard"
# Safe validation guidance only
```

#### Scenario 2: Your Home Lab (Standard Mode)
```bash
bhd-assist hypothesis-draft \
  --workspace . \
  --environment lab \
  --target-owner self \
  --assist-level standard

# Result: effective_assist_level="standard"
# Same safe guidance
```

#### Scenario 3: Your Home Lab (Deep Lab Mode)
```bash
bhd-assist hypothesis-draft \
  --workspace . \
  --environment lab \
  --authorized \
  --target-owner self \
  --assist-level deep_lab

# Result: effective_assist_level="deep_lab"
# Broader testing methodologies for lab
# STILL NO exploit code/payloads!
```

#### Scenario 4: CTF Competition (Deep Lab Mode)
```bash
bhd-assist hypothesis-draft \
  --workspace . \
  --environment ctf \
  --authorized \
  --target-owner self \
  --assist-level deep_lab

# Result: effective_assist_level="deep_lab"
# CTF-appropriate guidance
```

#### Scenario 5: Clamped Request (Safety in Action)
```bash
# Try to request deep_lab in production
bhd-assist hypothesis-draft \
  --workspace . \
  --environment prod_client \
  --assist-level deep_lab

# Result: effective_assist_level="standard" (clamped!)
# reasons: ["clamped: environment=prod_client (requires lab or ctf)"]
# System protects you from unsafe configuration
```

---

## LLM Provider Configuration

### Available Providers

1. **Ollama (Local, CPU - No API key needed)**
   ```bash
   # Install Ollama: https://ollama.ai
   ollama run llama3.2:1b

   # Then just use bhd-assist
   bhd-assist hypothesis-draft --workspace .
   ```

2. **OpenAI (Cloud - API key already configured)**
   ```bash
   # Your key is already in ~/.bashrc
   # Just use it:
   bhd-assist hypothesis-draft --workspace .
   ```

3. **Anthropic (Cloud - API key already configured)**
   ```bash
   # Your key is already in ~/.bashrc
   # Just use it:
   bhd-assist hypothesis-draft --workspace .
   ```

### Provider Order & Fallback

Default order: `ollama → openai → anthropic`

System tries each provider in order and falls back automatically:

```bash
# Use custom order
bhd-assist hypothesis-draft \
  --workspace . \
  --provider-order "openai,anthropic,ollama"

# Output shows which succeeded:
# "provider_used": "openai"
```

**What happens if no providers available?**
```
Error: No LLM providers available. Configure at least one of:
  - Ollama (local)
  - OpenAI API key
  - Anthropic API key
```

---

## All bhd-assist Commands

### 1. init - Initialize Workspace
```bash
bhd-assist init --workspace /path/to/project
```

### 2. ingest - Import Tool Output
```bash
# Nmap XML
bhd-assist ingest \
  --tool nmap \
  --file scan.xml \
  --workspace .

# Support planned: Burp Suite, nikto, etc.
```

### 3. playbook-list - Show Available Playbooks
```bash
# All playbooks
bhd-assist playbook-list

# Filter by test type
bhd-assist playbook-list --test-type web
bhd-assist playbook-list --test-type network
bhd-assist playbook-list --test-type ics
```

### 4. playbook-render - View Playbook Details
```bash
# Human-readable checklist
bhd-assist playbook-render exposed_admin_interfaces

# Evidence plan (JSON)
bhd-assist playbook-render idor_validation --format evidence

# Finding draft template
bhd-assist playbook-render authz_broken_access \
  --format finding \
  --asset "webapp.example.com"
```

### 5. suggest-playbooks - Auto-Select Playbook
```bash
# Basic suggestion
bhd-assist suggest-playbooks \
  --test-type network \
  --workspace .

# With explanation (debug mode)
bhd-assist suggest-playbooks \
  --test-type network \
  --workspace . \
  --explain
```

### 6. hypothesis-draft - Generate Hypotheses (NEW!)
```bash
# Basic (standard mode)
bhd-assist hypothesis-draft --workspace .

# Full context specification
bhd-assist hypothesis-draft \
  --workspace . \
  --environment prod_client \
  --target-owner client \
  --assist-level standard \
  --max 5

# Lab mode with all flags
bhd-assist hypothesis-draft \
  --workspace . \
  --environment lab \
  --authorized \
  --target-owner self \
  --assist-level deep_lab \
  --provider-order "ollama,openai,anthropic" \
  --max 3
```

### 7. export - Export Findings (Stub)
```bash
bhd-assist export --output findings.json
```

---

## All bhd-cli Commands (Main Engagement CLI)

### Engagement Management
```bash
bhd-cli init                          # Create new engagement
bhd-cli show                          # Show current engagement
bhd-cli engagements list              # List all engagements
bhd-cli engagements switch <name>     # Switch engagement
```

### Scope Management
```bash
bhd-cli add-target 192.168.1.100
bhd-cli note "Started reconnaissance phase"
```

### Phase Tracking
```bash
bhd-cli phase status                  # View all phases
bhd-cli phase set "Reconnaissance" in_progress
bhd-cli phase note "Reconnaissance" "Completed Nmap scan"
```

### Finding Management
```bash
bhd-cli finding add                   # Guided finding creation
bhd-cli finding list                  # List findings
bhd-cli finding show F-001            # View finding details
bhd-cli finding edit F-001            # Edit finding
bhd-cli finding delete F-001          # Delete finding
bhd-cli finding status F-001 remediated
bhd-cli finding filter --severity Critical
bhd-cli finding search "SQL injection"
```

### Home Audit
```bash
bhd-cli home-audit run                # Auto-generate home security findings
```

### Reporting
```bash
bhd-cli report                        # Generate report.md
bhd-cli export json                   # Export to JSON
bhd-cli export pdf                    # Export to PDF
```

---

## Example: Complete Pentest Session

```bash
# ============================
# SETUP
# ============================

# 1. Create project directory
mkdir ~/pentests/acme-corp-2026
cd ~/pentests/acme-corp-2026

# 2. Initialize bhd-cli engagement
cd ..
bhd-cli init
# Client: Acme Corp
# Project: Q1 2026 External Assessment
# Test type: network
# Scope: 203.0.113.0/24
# Authorization: yes
# ROE: No DoS, business hours only

# 3. Initialize bhd-assist workspace
cd acme-corp-2026
bhd-assist init --workspace .

# ============================
# RECONNAISSANCE & SCANNING
# ============================

# 4. Run Nmap
nmap -sV -p- 203.0.113.50 -oX nmap_scan.xml

# 5. Ingest results
bhd-assist ingest \
  --tool nmap \
  --file nmap_scan.xml \
  --workspace .

# ============================
# ANALYSIS (ADAPTIVE MODE)
# ============================

# 6. Generate hypotheses (production-safe)
bhd-assist hypothesis-draft \
  --workspace . \
  --environment prod_client \
  --target-owner client \
  --max 5 > hypotheses.json

# View hypotheses
cat hypotheses.json | python3 -m json.tool

# 7. Get playbook suggestions
bhd-assist suggest-playbooks \
  --test-type network \
  --workspace . \
  --explain > suggested_playbooks.json

# 8. View recommended playbook
bhd-assist playbook-render exposed_admin_interfaces

# ============================
# VALIDATION & DOCUMENTATION
# ============================

# 9. Follow playbook validation steps
# (Manual testing based on playbook guidance)

# 10. Add findings to engagement
cd ..
bhd-cli finding add
# Follow prompts based on hypotheses and validation...

# 11. Track progress
bhd-cli phase set "Scanning" complete
bhd-cli phase set "Enumeration" in_progress

# 12. Add notes
bhd-cli note "Found RDP exposed on 203.0.113.50:3389"

# ============================
# REPORTING
# ============================

# 13. Generate report
bhd-cli report
# Creates: engagements/acme-corp-*/report.md

# 14. Export
bhd-cli export json
bhd-cli export pdf  # Requires: pip install reportlab

# 15. Review
cat engagements/acme-corp-*/report.md
```

---

## Output Format Examples

### hypothesis-draft Output
```json
{
  "status": "success",
  "effective_assist_level": "standard",
  "reasons": ["requested_level=standard"],
  "provider_used": "openai",
  "hypotheses": [
    {
      "id": "a7f3c9e2b8d14fa6",
      "related_observations": ["b4c3793b7f53e4d4", "4030e676c73ebde0"],
      "title": "Exposed Administrative Services Increase Attack Surface",
      "description": "The target has RDP (3389) and SSH (22) exposed...",
      "risk_tags": ["exposure", "remote-admin", "authentication"],
      "confidence": 0.85,
      "rationale": "Based on observations b4c3793b7f53e4d4...",
      "requires_validation": true
    }
  ]
}
```

### suggest-playbooks Output (with --explain)
```json
{
  "status": "success",
  "test_type": "network",
  "observations_count": 2,
  "selected_playbook": "exposed_admin_interfaces",
  "evaluated_rules": [
    {
      "rule_id": "network_exposed_admin_service",
      "matched": true,
      "playbook_id": "exposed_admin_interfaces",
      "priority": 90
    },
    {
      "rule_id": "web_idor_detection",
      "matched": false,
      "failure_reasons": ["test_type 'network' not in rule test_types ['web']"]
    }
  ]
}
```

---

## Testing & Development

### Run Tests
```bash
cd ~/BlackHatDefenseLLC/bhd_app

# All assistant tests
pytest tests/assistant/ -v

# Specific test files
pytest tests/assistant/test_adaptive_mode.py -v
pytest tests/assistant/test_hypothesis_drafter.py -v
pytest tests/assistant/test_llm_router.py -v

# Quick run
pytest tests/assistant/ -q
```

### Load Keys for Testing
```bash
cd ~/BlackHatDefenseLLC/bhd_app
source load_keys.sh
```

---

## Troubleshooting

### "No LLM providers available"
```bash
# Check if keys are loaded
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Load them
source ~/.bashrc
# OR
source load_keys.sh

# Verify
python3 -c "import os; print('OK' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

### "bhd-assist: command not found"
```bash
# Reinstall
cd ~/BlackHatDefenseLLC/bhd_app
pip install -e .

# Verify
which bhd-assist
bhd-assist --help
```

### Provider Fails
```bash
# Check provider order and try different one
bhd-assist hypothesis-draft \
  --workspace . \
  --provider-order "anthropic,openai"  # Skip Ollama

# Or install Ollama for local processing
# https://ollama.ai
```

---

## Safety Reminders

### Always Blocked (All Modes)
- ❌ Exploit code generation
- ❌ Payload creation
- ❌ Bypass instructions
- ❌ Reverse shells / backdoors
- ❌ Malware / ransomware
- ❌ DoS techniques

### Always Allowed (All Modes)
- ✅ Validation checklists
- ✅ Evidence collection
- ✅ Risk assessment
- ✅ Threat modeling
- ✅ Safe verification strategies

### ADAPTIVE Mode Benefits
- Reduces false positives
- Allows normal security language
- Context-aware safety
- Automatic clamping to safe levels

---

## Quick Reference Card

```bash
# ============================================
# QUICK COMMANDS
# ============================================

# Initialize workspace
bhd-assist init --workspace .

# Ingest scan
bhd-assist ingest --tool nmap --file scan.xml --workspace .

# Generate hypotheses (safe)
bhd-assist hypothesis-draft --workspace .

# Generate hypotheses (lab mode)
bhd-assist hypothesis-draft \
  --workspace . \
  --environment lab \
  --authorized \
  --target-owner self \
  --assist-level deep_lab

# Get playbook
bhd-assist suggest-playbooks --test-type network --workspace .

# View playbook
bhd-assist playbook-render <playbook_id>

# Create engagement
bhd-cli init

# Add finding
bhd-cli finding add

# Generate report
bhd-cli report

# ============================================
# LOAD API KEYS
# ============================================
source ~/.bashrc
# OR
source load_keys.sh

# ============================================
# RUN TESTS
# ============================================
pytest tests/assistant/ -q
```

---

## What's New Today

### ADAPTIVE Mode System
- Context evaluation (environment, authorization, ownership)
- Automatic safety clamping
- Transparent reasoning

### LLM Integration
- Multi-provider support (Ollama, OpenAI, Anthropic)
- Automatic fallback
- Schema-guaranteed output

### Hypothesis Drafting
- Observation clustering
- Risk framing
- Evidence planning
- Policy-compliant output

### Improved Policy Guard
- Reduced false positives
- Still blocks weaponized content
- ADAPTIVE patterns

---

**Last Updated:** 2026-02-17
**Version:** 0.2.0 (ADAPTIVE)
**Status:** Production-ready

Need help? Check:
- `ADAPTIVE_MODE_IMPLEMENTATION.md` - Full technical details
- `src/bhd_cli/assistant/README.md` - Assistant documentation
- `bhd-assist --help` - Command reference
- `pytest tests/assistant/ -v` - Run tests
