# BHD.py Quick Start Guide

**Black Hat Defense CLI** - Penetration testing engagement and finding management tool.

---

## Installation & Setup

No dependencies required. Just Python 3.

```bash
cd ~/BlackHatDefenseLLC/bhd_app
python3 bhd.py --help
```

---

## Basic Workflow

### 1. Create New Engagement
```bash
python3 bhd.py init
```

You'll be prompted for:
- **Client name**: `HomeOwner`, `AcmeCorp`, etc.
- **Project name**: `Home Audit`, `Network Pentest`, etc.
- **Test type**: `home`, `web`, `network`, or `other`
- **In-scope targets**: `192.168.1.1`, `10.0.0.0/24` (comma-separated)
- **Out-of-scope** (optional): Anything explicitly excluded
- **Written authorization**: Must answer `yes` to proceed
- **Rules of engagement**: `No DoS, scan only, 9am-5pm windows`, etc.

---

### 2. Add Findings

#### Option A: Home Audit Wizard (for home networks)
```bash
python3 bhd.py home-audit run
```

Interactive questionnaire about:
- Router make/model, IP, firmware
- WiFi security mode (WPA3/WPA2/WEP/Open)
- WPS, UPnP, remote admin status
- Password strength, guest network, IoT segmentation
- DNS filtering, port forwards
- **WAN exposure**: Choose `1`/`2`/`3` or type `y`/`n`/`u`

Auto-generates findings based on answers.

#### Option B: Manual Finding Entry
```bash
python3 bhd.py finding add
```

Guided process:
1. Enter title, target, description
2. Choose **Impact**: Critical/High/Medium/Low/Informational (with coaching)
3. Choose **Likelihood**: High/Medium/Low (with coaching)
4. Auto-calculates severity and remediation priority
5. Enter evidence, business impact, recommendation
6. Validates input before saving

---

### 3. Manage Findings

#### List all findings (sorted by ID, with status)
```bash
python3 bhd.py finding list
```

Output format:
```
- F-001 [High] (open) Title — Target
- F-002 [Medium] (remediated) Title — Target
```

#### Show detailed finding
```bash
python3 bhd.py finding show F-001
```

Displays: severity, impact, likelihood, priority, target, status, timestamps, description, evidence, business impact, recommendation.

#### Search by keyword
```bash
python3 bhd.py finding search "password"
python3 bhd.py finding search "SSH"
python3 bhd.py finding search "10.168.168.1"
```

Searches across: title, description, evidence, business impact, recommendation, affected target.

#### Filter findings
```bash
# By severity
python3 bhd.py finding filter --severity Critical
python3 bhd.py finding filter --severity High

# By target
python3 bhd.py finding filter --target "192.168.1.1"

# By status
python3 bhd.py finding filter --status open
python3 bhd.py finding filter --status remediated

# Combine filters
python3 bhd.py finding filter --severity High --status open
```

**Status values:**
- `open` - Default, not yet fixed
- `remediated` - Client has fixed the issue
- `accepted` - Risk accepted, won't fix
- `retest` - Needs retesting after remediation

#### Edit finding
```bash
python3 bhd.py finding edit F-001
```

- Press Enter to keep current value
- Type new value to change
- Can update risk scoring (impact/likelihood) - recalculates severity
- Validates fields before saving
- Auto-converts IP commas: `10,168,168,1` → `10.168.168.1`

#### Update finding status
```bash
python3 bhd.py finding status F-001 remediated
python3 bhd.py finding status F-002 accepted
python3 bhd.py finding status F-003 retest
python3 bhd.py finding status F-004 open
```

#### Delete finding
```bash
python3 bhd.py finding delete F-099
```

Confirms before deleting.

---

### 4. Track Progress (Methodology Phases)

#### View phase status
```bash
python3 bhd.py phase status
```

Shows all phases with coaching text:
- Pre-Engagement
- Reconnaissance
- Scanning
- Enumeration
- Vulnerability Analysis
- Exploitation
- Reporting

#### Update phase
```bash
python3 bhd.py phase set "Scanning" in_progress
python3 bhd.py phase set "Scanning" complete
```

Phase names are case-sensitive. Copy exact names from `phase status`.

#### Add phase note
```bash
python3 bhd.py phase note "Scanning" "Completed nmap scan of all in-scope targets"
```

---

### 5. Generate Report
```bash
python3 bhd.py report
```

Creates `report.md` in the engagement folder with:
- Executive summary with severity breakdown
- Scope and rules of engagement
- Methodology phase status
- Findings summary table (sorted by ID)
- Detailed findings (sorted by ID)
- Engagement notes

**Deterministic output:** Findings always appear in ID order (F-001, F-002, F-003...) regardless of when they were added/edited.

---

### 6. Manage Multiple Engagements

#### List all engagements
```bash
python3 bhd.py engagements list
```

Shows: client, project, type, finding count, current marker.

#### Switch engagement
```bash
python3 bhd.py engagements switch client-project-20260215-123456
```

Changes active engagement. All subsequent commands operate on the new engagement.

#### Show current engagement
```bash
python3 bhd.py show
```

Displays: client, project, type, created date, scope, ROE, notes count, findings count.

---

## Command Reference

### Engagements
| Command | Description |
|---------|-------------|
| `engagements list` | Show all engagements |
| `engagements switch <name>` | Switch to engagement |
| `init` | Create new engagement |
| `show` | Show current engagement |

### Findings (8 commands)
| Command | Description |
|---------|-------------|
| `finding add` | Add new finding (guided) |
| `finding list` | List all findings (sorted by ID, with status) |
| `finding show <ID>` | Show full finding details |
| `finding edit <ID>` | Edit finding (with validation) |
| `finding delete <ID>` | Delete finding |
| `finding status <ID> <status>` | Update finding status |
| `finding filter [options]` | Filter findings |
| `finding search <keyword>` | Search findings |

### Phases
| Command | Description |
|---------|-------------|
| `phase status` | Show all phases |
| `phase set <phase> <status>` | Update phase (not_started/in_progress/complete) |
| `phase note <phase> <text>` | Add phase note |

### Other
| Command | Description |
|---------|-------------|
| `add-target <IP>` | Add target to scope |
| `note <text>` | Add general note |
| `home-audit run` | Run home audit wizard |
| `report` | Generate report.md |

---

## Real-World Example

### Test 10.168.168.1 (home router)
```bash
# 1. Create engagement
python3 bhd.py init
# Client: HomeOwner
# Project: Home Security Audit
# Type: home
# Targets: 10.168.168.1
# Authorization: yes
# ROE: No DoS, scan for vulnerabilities

# 2. Run home audit wizard
python3 bhd.py home-audit run
# Answer questions about router, WiFi, etc.

# 3. Review auto-generated findings
python3 bhd.py finding list

# 4. Filter by severity
python3 bhd.py finding filter --severity Medium

# 5. Add custom finding from manual testing
python3 bhd.py finding add
# Title: SSH Service Exposed
# Target: 10.168.168.1
# Description: SSH service running on non-standard port 2222
# Evidence: nmap scan shows 2222/tcp open ssh
# ...

# 6. Generate report
python3 bhd.py report

# Report saved to: engagements/homeowner-home-security-audit-20260215-123456/report.md
```

---

## Multi-Client Workflow

```bash
# Morning - Client A
python3 bhd.py engagements list
python3 bhd.py engagements switch clienta-pentest-20260215-090000
python3 bhd.py finding filter --status open
python3 bhd.py finding add

# Afternoon - Client B
python3 bhd.py engagements switch clientb-webapp-20260215-140000
python3 bhd.py finding list
python3 bhd.py report

# End of day - check all clients
python3 bhd.py engagements list
```

---

## Tips & Best Practices

1. **Add findings as you discover them** - Don't wait until the end of testing
2. **Use search before adding** - Avoid duplicates: `python3 bhd.py finding search "SSH"`
3. **Update phases regularly** - Shows methodology in report, tracks progress
4. **Filter for focus** - Use `--severity High --status open` for priorities
5. **finding show is your friend** - Quick reference during client calls
6. **Status tracking matters** - Update status after client remediation for accurate reporting
7. **Deterministic reports** - Findings always sorted by ID, safe to edit/delete/reorder

---

## Data Storage

All data stored in JSON format:
```
engagements/
├── .current                                    # Current engagement pointer
├── client-project-20260215-123456/
│   ├── engagement.json                        # All engagement data
│   └── report.md                              # Generated report
```

**No database required.** Files are human-readable and can be version-controlled with git.

---

## Troubleshooting

### "No current engagement"
```bash
python3 bhd.py engagements list
python3 bhd.py engagements switch <name>
# OR
python3 bhd.py init  # Create new one
```

### "Finding not found"
```bash
python3 bhd.py finding list  # Check exact ID format (F-001, F-002, etc.)
```

### "Phase not found"
```bash
python3 bhd.py phase status  # Copy exact phase name (case-sensitive)
```

---

## Getting Help

```bash
# General help
python3 bhd.py --help

# Command-specific help
python3 bhd.py finding --help
python3 bhd.py engagements --help
python3 bhd.py phase --help

# Subcommand help
python3 bhd.py finding filter --help
python3 bhd.py finding status --help
```

---

## Summary of Key Features

**6 Core Enhancements:**
1. ✅ Finding edit - Fix typos, update details, change risk scoring
2. ✅ Finding delete - Remove mistakes and duplicates
3. ✅ Finding search - Keyword search across all fields
4. ✅ Finding filter - Filter by severity/target/status
5. ✅ Finding show - Display full finding details
6. ✅ Finding status - Track remediation progress

**Additional Features:**
- ✅ Engagements list/switch - Multi-client management
- ✅ Validation on edit - Prevents bad data
- ✅ Deterministic reports - Findings sorted by ID
- ✅ Home audit wizard - Quick home network assessments
- ✅ Phase tracking - Methodology documentation
- ✅ Risk scoring with coaching - Standardized severity ratings

**Ready to use!** Start with `python3 bhd.py init` 🚀
