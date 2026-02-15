#!/usr/bin/env python3
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENG_DIR = BASE_DIR / "engagements"
CURRENT_FILE = ENG_DIR / ".current"


# --------------------------
# Utilities / Storage
# --------------------------
def ensure_dirs():
    ENG_DIR.mkdir(parents=True, exist_ok=True)


def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def slugify(name: str) -> str:
    keep = []
    for ch in name.strip().lower():
        if ch.isalnum():
            keep.append(ch)
        elif ch in (" ", "-", "_"):
            keep.append("-")
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "engagement"


def pick_current_engagement() -> Path:
    if not CURRENT_FILE.exists():
        print("No current engagement selected. Run: python3 bhd.py init", file=sys.stderr)
        sys.exit(1)
    rel = CURRENT_FILE.read_text().strip()
    p = (ENG_DIR / rel).resolve()
    if not p.exists():
        print("Current engagement folder missing. Run: python3 bhd.py init", file=sys.stderr)
        sys.exit(1)
    return p


def load_engagement(p: Path) -> dict:
    f = p / "engagement.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text())


def save_engagement(p: Path, data: dict):
    f = p / "engagement.json"
    f.write_text(json.dumps(data, indent=2, sort_keys=False))


def safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except (KeyboardInterrupt, EOFError):
        print("\nCanceled.")
        sys.exit(1)


def choose_from(prompt: str, options: list[str]) -> str:
    while True:
        print(prompt)
        for i, opt in enumerate(options, 1):
            print(f"  {i}) {opt}")
        raw = safe_input("> ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        print("Pick a valid number.\n")


def choose_yes_no_unknown(prompt: str) -> str:
    """
    Choose from No/Yes/Unknown with support for:
    - Numeric input: 1/2/3
    - Shortcut input: n/y/u (case-insensitive)
    Returns: "No", "Yes", or "Unknown"
    """
    while True:
        print(prompt)
        print("  1) No")
        print("  2) Yes")
        print("  3) Unknown")
        raw = safe_input("> ").strip().lower()

        # Accept numeric input
        if raw.isdigit():
            idx = int(raw)
            if idx == 1:
                return "No"
            elif idx == 2:
                return "Yes"
            elif idx == 3:
                return "Unknown"

        # Accept y/n/u shortcuts
        if raw in ("n", "no"):
            return "No"
        if raw in ("y", "yes"):
            return "Yes"
        if raw in ("u", "unknown"):
            return "Unknown"

        print("Pick 1/2/3 or type y/n/u.\n")


def yes_no(prompt: str) -> bool:
    while True:
        raw = safe_input(prompt + " (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("Type y or n.\n")


# --------------------------
# Methodology / Phases
# --------------------------
PHASES = [
    ("Pre-Engagement", "Scope, written authorization, and ROE. This protects you legally and keeps work aligned."),
    ("Reconnaissance", "Passive/active discovery to understand the target surface before touching it harder."),
    ("Scanning", "Identify open ports/services and basic versions. This is your map of the environment."),
    ("Enumeration", "Go deeper on discovered services (endpoints, shares, users, configs). This is where findings are born."),
    ("Vulnerability Analysis", "Translate observed conditions into likely weaknesses and risk hypotheses."),
    ("Exploitation", "Only if authorized. Minimal-impact proof. Capture evidence, don’t ‘go wild’."),
    ("Reporting", "Convert technical results into risk + remediation. This is what clients pay for."),
]


def default_phase_state():
    return {name: {"status": "not_started", "updated_utc": None, "notes": []} for name, _ in PHASES}


def phase_coaching_text(phase_name: str) -> str:
    for name, why in PHASES:
        if name == phase_name:
            return why
    return ""


def get_phase_state(data: dict) -> dict:
    meth = data.setdefault("methodology", {})
    phases = meth.setdefault("phases", default_phase_state())
    for name, _why in PHASES:
        phases.setdefault(name, {"status": "not_started", "updated_utc": None, "notes": []})
    return phases


# --------------------------
# Risk Coaching
# --------------------------
IMPACT_GUIDE = {
    "Critical": [
        "Full system compromise (root/DA) on a production asset",
        "Sensitive data exposure at scale (PII/PHI/PCI/source code)",
        "Material business disruption (outage, ransomware staging, safety impact in OT)",
    ],
    "High": [
        "Authentication bypass or strong privilege escalation on important systems",
        "Sensitive data readable/alterable (but not necessarily at massive scale)",
        "Remote code execution with meaningful reach",
    ],
    "Medium": [
        "Limited data exposure, partial access, or constrained privilege escalation",
        "Exploitation requires specific conditions or has limited blast radius",
    ],
    "Low": [
        "Minor misconfigurations with little real-world leverage",
        "Hard to chain into anything serious",
    ],
    "Informational": [
        "Useful intel / hygiene issue, but not a direct security weakness by itself",
    ],
}

LIKELIHOOD_GUIDE = {
    "High": [
        "Remote exploitable, no creds required, common tooling works",
        "Reliable and repeatable; attacker skill barrier is low",
    ],
    "Medium": [
        "Needs creds, user interaction, specific configuration, or partial access",
        "Exploit works but conditions aren’t always present",
    ],
    "Low": [
        "Hard to exploit, requires chaining multiple steps, rare conditions",
        "Unreliable or noisy; high chance an attacker fails or gets detected",
    ],
}


def severity_from(impact: str, likelihood: str) -> str:
    if impact == "Informational":
        return "Informational"
    if impact == "Critical":
        return "Critical" if likelihood in ("High", "Medium") else "High"
    if impact == "High":
        return "Critical" if likelihood == "High" else "High" if likelihood == "Medium" else "Medium"
    if impact == "Medium":
        return "High" if likelihood == "High" else "Medium" if likelihood == "Medium" else "Low"
    if impact == "Low":
        return "Low"
    return "Medium"


def remediation_priority(severity: str) -> str:
    return {
        "Critical": "Immediate (0–7 days)",
        "High": "High (7–30 days)",
        "Medium": "Planned (30–90 days)",
        "Low": "Backlog (90+ days)",
        "Informational": "As appropriate",
    }.get(severity, "Planned (30–90 days)")


def print_impact_coaching():
    print("\nImpact coaching (what would happen to the client if abused):")
    for k, bullets in IMPACT_GUIDE.items():
        print(f"  {k}:")
        for b in bullets:
            print(f"    - {b}")


def print_likelihood_coaching():
    print("\nLikelihood coaching (how realistic exploitation is):")
    for k, bullets in LIKELIHOOD_GUIDE.items():
        print(f"  {k}:")
        for b in bullets:
            print(f"    - {b}")


# --------------------------
# Guardrails / Validation
# --------------------------
BANNED_TITLES = {
    "not started", "not_started", "todo", "tbd", "test", "asdf",
    "pre-engagement not started", "recon not started", "scanning not started"
}
BANNED_TITLE_KEYWORDS = {"not started", "not_started", "phase", "methodology", "wizard"}
WIZARD_MARKERS = {
    "=== black hat defense cli", "client name:", "project name:", "test type:",
    "in-scope targets", "out-of-scope", "rules of engagement", "do you have written authorization"
}
PHASE_WORDS = {p[0].lower() for p in PHASES} | {
    "pre-engagement", "reconnaissance", "scanning", "enumeration",
    "vulnerability analysis", "exploitation", "reporting"
}


def looks_like_wizard_output(s: str) -> bool:
    s2 = s.strip().lower()
    return any(m in s2 for m in WIZARD_MARKERS)


def looks_like_phase_dump(s: str) -> bool:
    s2 = s.strip().lower()
    hits = 0
    for w in PHASE_WORDS:
        if w in s2:
            hits += 1
    return hits >= 3  # if they paste multiple phase names, it's probably a dump


def validate_finding_fields(title: str, description: str, evidence: str, business_impact: str, recommendation: str) -> list[str]:
    errors = []

    t = title.strip().lower()
    if not title.strip() or len(title.strip()) < 6:
        errors.append("Title is too short. Make it specific (e.g., 'UPnP Enabled on Router').")
    if t in BANNED_TITLES or any(k in t for k in BANNED_TITLE_KEYWORDS):
        errors.append("Title looks like a placeholder/process note. Findings must describe a security issue, not workflow status.")

    if not description.strip() or len(description.strip()) < 20:
        errors.append("Description is too short. Describe the actual security condition and where it occurs.")
    if looks_like_phase_dump(description) or looks_like_wizard_output(description):
        errors.append("Description looks like phase/wizard output. Put the security issue, not the tool prompts.")

    if not evidence.strip() or len(evidence.strip()) < 10:
        errors.append("Evidence is too short. Record what you observed (ports, settings, URLs, screenshots note).")
    if looks_like_wizard_output(evidence):
        errors.append("Evidence looks like wizard output. Evidence should be observations/results, not 'I ran init'.")
    if "python3 bhd.py init" in evidence.lower():
        errors.append("Evidence is 'init'. Replace with actual evidence (e.g., router setting screenshot note, scan results summary).")

    if not business_impact.strip() or len(business_impact.strip()) < 20:
        errors.append("Business Impact is too short. Explain impact in plain English (1–3 sentences).")
    if looks_like_wizard_output(business_impact):
        errors.append("Business Impact looks like tool output. Business Impact should be plain English risk to the client.")

    if not recommendation.strip() or len(recommendation.strip()) < 15:
        errors.append("Recommendation is too short. Provide an actionable fix (disable X, update Y, change config Z).")
    if looks_like_wizard_output(recommendation):
        errors.append("Recommendation looks like tool output. Recommendation should be how to fix the issue.")

    return errors


# --------------------------
# Finding ID + Auto-Finding Cleanup (FIXES)
# --------------------------
def clear_auto_findings(data: dict):
    """
    Remove any auto-generated findings (e.g., home-audit wizard) so re-running the wizard
    produces a clean, current snapshot instead of duplicating old results.
    """
    work = data.setdefault("work", {})
    findings = work.setdefault("findings", [])
    work["findings"] = [f for f in findings if not f.get("auto_generated")]


def next_finding_id(findings: list[dict]) -> str:
    """
    Generate the next sequential F-### ID based on the max existing ID.
    This stays stable even if findings are removed (e.g., clearing auto findings).
    """
    max_num = 0
    for f in findings:
        m = re.match(r"F-(\d+)$", str(f.get("id", "")))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"F-{max_num + 1:03d}"


def finding_sort_key(f: dict) -> int:
    """
    Extract numeric ID from finding for sorting (F-001 -> 1, F-023 -> 23).
    Returns 999 for malformed IDs.
    """
    fid = f.get("id", "F-999")
    m = re.match(r"F-(\d+)", fid)
    return int(m.group(1)) if m else 999


# --------------------------
# Commands (Core)
# --------------------------
def cmd_engagements_list(_args):
    ensure_dirs()
    eng_dirs = [d for d in ENG_DIR.iterdir() if d.is_dir()]

    if not eng_dirs:
        print("No engagements yet. Run: python3 bhd.py init")
        return

    current = ""
    if CURRENT_FILE.exists():
        current = CURRENT_FILE.read_text().strip()

    print("=== Engagements ===")
    for eng_dir in sorted(eng_dirs):
        marker = " ← CURRENT" if eng_dir.name == current else ""
        data = load_engagement(eng_dir)
        meta = data.get("meta", {})
        findings_count = len(data.get("work", {}).get("findings", []))
        print(f"\n{eng_dir.name}{marker}")
        print(f"  Client: {meta.get('client', 'N/A')}")
        print(f"  Project: {meta.get('project', 'N/A')}")
        print(f"  Type: {meta.get('test_type', 'N/A')}")
        print(f"  Findings: {findings_count}")


def cmd_engagements_switch(args):
    ensure_dirs()
    eng_name = args.name
    eng_path = ENG_DIR / eng_name

    if not eng_path.exists():
        print(f"Engagement not found: {eng_name}", file=sys.stderr)
        print("\nAvailable engagements:")
        for eng_dir in sorted(ENG_DIR.iterdir()):
            if eng_dir.is_dir():
                print(f"  - {eng_dir.name}")
        sys.exit(1)

    CURRENT_FILE.write_text(eng_name)
    print(f"Switched to: {eng_name}")


def cmd_init(_args):
    ensure_dirs()

    print("=== Black Hat Defense CLI — New Engagement Wizard ===")
    client = safe_input("Client name: ").strip()
    project = safe_input("Project name: ").strip()
    test_type = safe_input("Test type (web/network/home/other): ").strip() or "other"

    scope_in = safe_input("In-scope targets (comma-separated IPs/domains/CIDRs): ").strip()
    out_scope = safe_input("Out-of-scope notes (optional): ").strip()

    # Scope sanity warning (especially for home jobs)
    if test_type.lower() == "home":
        if re.search(r"\b0\.0\.0\.0/0\b", scope_in) or "internet" in scope_in.lower():
            print("\nWARNING: Your scope looks too broad for a home audit. Scope should be your home network / devices only.\n")

    auth = safe_input("Do you have written authorization? (yes/no): ").strip().lower()
    if auth not in ("yes", "y"):
        print("Stop. Don’t run anything without written authorization.")
        sys.exit(1)

    rules = safe_input("Rules of engagement notes (e.g., no DoS, time windows): ").strip()

    engagement_name = f"{slugify(client)}-{slugify(project)}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    folder = ENG_DIR / engagement_name
    folder.mkdir(parents=True, exist_ok=True)

    targets = [t.strip() for t in scope_in.split(",") if t.strip()]

    data = {
        "meta": {
            "created_utc": now_iso(),
            "client": client,
            "project": project,
            "test_type": test_type,
        },
        "scope": {
            "in_scope": targets,
            "out_of_scope": out_scope,
            "rules_of_engagement": rules,
        },
        "methodology": {
            "phases": default_phase_state()
        },
        "work": {
            "notes": [],
            "findings": []
        }
    }

    save_engagement(folder, data)
    CURRENT_FILE.write_text(engagement_name)

    print(f"\nCreated engagement: {engagement_name}")
    print("Next: python3 bhd.py phase status | python3 bhd.py home-audit run | python3 bhd.py finding add | python3 bhd.py report")


def cmd_show(_args):
    p = pick_current_engagement()
    data = load_engagement(p)
    meta = data.get("meta", {})
    scope = data.get("scope", {})
    work = data.get("work", {})

    print("=== Current Engagement ===")
    print(f"Folder: {p.name}")
    print(f"Client: {meta.get('client','')}")
    print(f"Project: {meta.get('project','')}")
    print(f"Type: {meta.get('test_type','')}")
    print(f"Created: {meta.get('created_utc','')}")
    print("\n--- Scope ---")
    for t in scope.get("in_scope", []):
        print(f"  IN:  {t}")
    if scope.get("out_of_scope"):
        print(f"  OUT: {scope.get('out_of_scope')}")
    if scope.get("rules_of_engagement"):
        print(f"\nROE: {scope.get('rules_of_engagement')}")

    print("\n--- Work ---")
    print(f"Notes: {len(work.get('notes', []))}")
    print(f"Findings: {len(work.get('findings', []))}")


def cmd_add_target(args):
    p = pick_current_engagement()
    data = load_engagement(p)

    target = args.target.strip()
    if not target:
        print("No target provided.", file=sys.stderr)
        sys.exit(1)

    scope = data.setdefault("scope", {})
    ins = scope.setdefault("in_scope", [])
    if target in ins:
        print("Target already in scope.")
        return
    ins.append(target)
    save_engagement(p, data)
    print(f"Added in-scope target: {target}")


def cmd_note(args):
    p = pick_current_engagement()
    data = load_engagement(p)

    note_text = args.text.strip()
    if not note_text:
        print("Empty note.", file=sys.stderr)
        sys.exit(1)

    work = data.setdefault("work", {})
    notes = work.setdefault("notes", [])
    notes.append({"ts_utc": now_iso(), "text": note_text})
    save_engagement(p, data)
    print("Note saved.")


# --------------------------
# Phase commands
# --------------------------
def cmd_phase_status(_args):
    p = pick_current_engagement()
    data = load_engagement(p)
    phases = get_phase_state(data)

    print("=== Phase Status ===")
    for name, why in PHASES:
        st = phases.get(name, {}).get("status", "not_started")
        upd = phases.get(name, {}).get("updated_utc") or "-"
        print(f"- {name}: {st} (updated {upd})")
        print(f"  Why it matters: {why}")
    save_engagement(p, data)


def cmd_phase_set(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    phases = get_phase_state(data)

    phase_name = args.phase
    if phase_name not in phases:
        print("Unknown phase. Use: python3 bhd.py phase status", file=sys.stderr)
        sys.exit(1)

    new_status = args.status
    if new_status not in ("not_started", "in_progress", "complete"):
        print("Status must be: not_started | in_progress | complete", file=sys.stderr)
        sys.exit(1)

    phases[phase_name]["status"] = new_status
    phases[phase_name]["updated_utc"] = now_iso()
    save_engagement(p, data)

    print(f"Phase updated: {phase_name} -> {new_status}")
    print(f"Coaching: {phase_coaching_text(phase_name)}")


def cmd_phase_note(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    phases = get_phase_state(data)

    phase_name = args.phase
    if phase_name not in phases:
        print("Unknown phase. Use: python3 bhd.py phase status", file=sys.stderr)
        sys.exit(1)

    text = args.text.strip()
    if not text:
        print("Empty phase note.", file=sys.stderr)
        sys.exit(1)

    phases[phase_name].setdefault("notes", []).append({"ts_utc": now_iso(), "text": text})
    phases[phase_name]["updated_utc"] = now_iso()
    save_engagement(p, data)
    print("Phase note saved.")


# --------------------------
# Finding commands
# --------------------------
def cmd_finding_add(_args):
    p = pick_current_engagement()
    data = load_engagement(p)

    print("=== Add Finding (guided + validated) ===")
    while True:
        title = safe_input("Title (short, specific): ").strip()
        affected = safe_input("Affected target (IP/host/app/device): ").strip()
        description = safe_input("Description (what is the security issue?): ").strip()

        print("\n--- Coaching ---")
        print_impact_coaching()
        impact = choose_from("\nChoose Impact:", ["Critical", "High", "Medium", "Low", "Informational"])

        print_likelihood_coaching()
        likelihood = choose_from("\nChoose Likelihood:", ["High", "Medium", "Low"])

        sev = severity_from(impact, likelihood)
        prio = remediation_priority(sev)

        print("\n--- Result ---")
        print(f"Calculated Severity: {sev}")
        print(f"Remediation Priority: {prio}")

        evidence = safe_input("\nEvidence (what you observed; not tool prompts): ").strip()
        business_impact = safe_input("Business impact (plain English, 1–3 sentences): ").strip()
        recommendation = safe_input("Recommendation (actionable fix): ").strip()

        errors = validate_finding_fields(title, description, evidence, business_impact, recommendation)
        if errors:
            print("\nNOPE. Fix these before saving the finding:")
            for e in errors:
                print(f"- {e}")
            print("\nTry again. (This is your training loop.)\n")
            continue

        findings = data.setdefault("work", {}).setdefault("findings", [])
        finding = {
            "id": next_finding_id(findings),
            "ts_utc": now_iso(),
            "title": title,
            "affected_target": affected,
            "description": description,
            "impact_level": impact,
            "likelihood": likelihood,
            "severity": sev,
            "remediation_priority": prio,
            "business_impact": business_impact,
            "evidence": evidence,
            "recommendation": recommendation,
            "status": "open",
        }
        findings.append(finding)
        save_engagement(p, data)
        print(f"\nFinding saved: {finding['id']} — {finding['title']}")
        break


def cmd_finding_list(_args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    if not findings:
        print("No findings yet.")
        return

    findings_sorted = sorted(findings, key=finding_sort_key)

    print("=== Findings ===")
    for f in findings_sorted:
        status = f.get('status', 'open')
        print(f"- {f.get('id')} [{f.get('severity')}] ({status}) {f.get('title')} — {f.get('affected_target')}")


def cmd_finding_edit(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    finding_id = args.id
    found = None
    found_idx = None
    for i, f in enumerate(findings):
        if f.get("id") == finding_id:
            found = f
            found_idx = i
            break

    if not found:
        print(f"Finding {finding_id} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"=== Editing {finding_id} ===")
    print("Press Enter to keep current value.\n")

    # Edit each field
    title = safe_input(f"Title [{found['title']}]: ").strip()
    if title:
        found['title'] = title

    affected = safe_input(f"Affected [{found['affected_target']}]: ").strip()
    if affected:
        # Fix IP comma issue
        affected = affected.replace(",", ".").strip()
        found['affected_target'] = affected

    description = safe_input(f"Description [{found['description'][:50]}...]: ").strip()
    if description:
        found['description'] = description

    # Allow editing impact/likelihood
    if yes_no("Update risk scoring (impact/likelihood)?"):
        print_impact_coaching()
        impact = choose_from("\nChoose Impact:", ["Critical", "High", "Medium", "Low", "Informational"])
        print_likelihood_coaching()
        likelihood = choose_from("\nChoose Likelihood:", ["High", "Medium", "Low"])

        # Recalculate severity and priority
        sev = severity_from(impact, likelihood)
        prio = remediation_priority(sev)

        found['impact_level'] = impact
        found['likelihood'] = likelihood
        found['severity'] = sev
        found['remediation_priority'] = prio

        print(f"\nRecalculated Severity: {sev}")
        print(f"Remediation Priority: {prio}")

    evidence = safe_input(f"\nEvidence [{found['evidence'][:50]}...]: ").strip()
    if evidence:
        found['evidence'] = evidence

    business_impact = safe_input(f"Business Impact [{found['business_impact'][:50]}...]: ").strip()
    if business_impact:
        found['business_impact'] = business_impact

    recommendation = safe_input(f"Recommendation [{found['recommendation'][:50]}...]: ").strip()
    if recommendation:
        found['recommendation'] = recommendation

    # Validate edited finding
    errors = validate_finding_fields(
        found['title'],
        found['description'],
        found['evidence'],
        found['business_impact'],
        found['recommendation']
    )

    if errors:
        print("\nValidation errors found:")
        for e in errors:
            print(f"- {e}")
        if not yes_no("\nSave anyway?"):
            print("Edit canceled.")
            return

    findings[found_idx] = found
    data["work"]["findings"] = findings
    save_engagement(p, data)
    print(f"\nUpdated finding {finding_id}")


def cmd_finding_delete(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    finding_id = args.id
    found = None
    for f in findings:
        if f.get("id") == finding_id:
            found = f
            break

    if not found:
        print(f"Finding {finding_id} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"About to delete: {found['id']} - {found['title']}")
    if not yes_no("Are you sure?"):
        print("Canceled.")
        return

    data["work"]["findings"] = [f for f in findings if f.get("id") != finding_id]
    save_engagement(p, data)
    print(f"Deleted finding {finding_id}")


def cmd_finding_filter(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    filtered = findings

    if args.severity:
        filtered = [f for f in filtered if f.get("severity") == args.severity]

    if args.target:
        filtered = [f for f in filtered if args.target.lower() in f.get("affected_target", "").lower()]

    if args.status:
        filtered = [f for f in filtered if f.get("status") == args.status]

    if not filtered:
        print("No findings match your filters.")
        return

    # Sort filtered results by ID for deterministic output
    filtered = sorted(filtered, key=finding_sort_key)

    print(f"=== Findings (filtered: {len(filtered)} of {len(findings)}) ===")
    for f in filtered:
        auto = " [AUTO]" if f.get("auto_generated") else ""
        print(f"- {f.get('id')} [{f.get('severity')}] {f.get('title')}{auto}")
        print(f"  Target: {f.get('affected_target')}")


def cmd_finding_search(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    query = args.query.lower()
    matched = []

    for f in findings:
        searchable = " ".join([
            f.get("title", ""),
            f.get("description", ""),
            f.get("evidence", ""),
            f.get("recommendation", ""),
            f.get("business_impact", ""),
            f.get("affected_target", ""),
        ]).lower()

        if query in searchable:
            matched.append(f)

    if not matched:
        print(f"No findings match '{args.query}'")
        return

    print(f"=== Search Results: '{args.query}' ({len(matched)} found) ===")
    for f in matched:
        print(f"\n{f.get('id')} [{f.get('severity')}] {f.get('title')}")
        print(f"  Target: {f.get('affected_target')}")
        desc_snippet = f.get('description', '')[:100]
        print(f"  Description: {desc_snippet}...")


def cmd_finding_show(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    finding_id = args.id
    found = None
    for f in findings:
        if f.get("id") == finding_id:
            found = f
            break

    if not found:
        print(f"Finding {finding_id} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"=== {found['id']} — {found['title']} ===\n")
    print(f"Severity: {found.get('severity', 'N/A')}")
    print(f"Impact Level: {found.get('impact_level', 'N/A')}")
    print(f"Likelihood: {found.get('likelihood', 'N/A')}")
    print(f"Remediation Priority: {found.get('remediation_priority', 'N/A')}")
    print(f"Affected Target: {found.get('affected_target', 'N/A')}")
    print(f"Status: {found.get('status', 'open')}")
    if found.get("auto_generated"):
        print(f"Auto-Generated: Yes")
    print(f"Created: {found.get('ts_utc', 'N/A')}\n")

    print("Description:")
    print(f"  {found.get('description', 'N/A')}\n")

    print("Evidence:")
    print(f"  {found.get('evidence', 'N/A')}\n")

    print("Business Impact:")
    print(f"  {found.get('business_impact', 'N/A')}\n")

    print("Recommendation:")
    print(f"  {found.get('recommendation', 'N/A')}")


def cmd_finding_status(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    finding_id = args.id
    new_status = args.status

    found = None
    found_idx = None
    for i, f in enumerate(findings):
        if f.get("id") == finding_id:
            found = f
            found_idx = i
            break

    if not found:
        print(f"Finding {finding_id} not found.", file=sys.stderr)
        sys.exit(1)

    old_status = found.get("status", "open")
    found["status"] = new_status

    findings[found_idx] = found
    data["work"]["findings"] = findings
    save_engagement(p, data)

    print(f"Updated {finding_id} status: {old_status} → {new_status}")


# --------------------------
# Home Audit (auto-findings)
# --------------------------
def add_finding_auto(data: dict, title: str, affected: str, description: str,
                     impact: str, likelihood: str, evidence: str, biz_impact: str, recommendation: str):
    sev = severity_from(impact, likelihood)
    prio = remediation_priority(sev)
    findings = data.setdefault("work", {}).setdefault("findings", [])
    finding = {
        "id": next_finding_id(findings),
        "ts_utc": now_iso(),
        "title": title,
        "affected_target": affected,
        "description": description,
        "impact_level": impact,
        "likelihood": likelihood,
        "severity": sev,
        "remediation_priority": prio,
        "business_impact": biz_impact,
        "evidence": evidence,
        "recommendation": recommendation,
        "status": "open",
        "auto_generated": True,
    }
    findings.append(finding)


def cmd_home_audit_run(_args):
    p = pick_current_engagement()
    data = load_engagement(p)

    # FIX: Re-running the home-audit should not duplicate old auto findings.
    clear_auto_findings(data)

    meta = data.get("meta", {})
    test_type = (meta.get("test_type", "") or "").lower()

    if test_type != "home":
        print("WARNING: This engagement test_type is not 'home'. Home audit can still run, but check your scope/ROE.\n")

    print("=== Home Audit Wizard (auto-generates findings) ===")
    router_make = safe_input("Router make/model (e.g., TP-Link Archer AX55): ").strip()
    router_ip = safe_input("Router IP (e.g., 192.168.1.1): ").strip()
    fw_known = yes_no("Do you know the router firmware version?")
    fw_ver = safe_input("Firmware version (or 'unknown'): ").strip() if fw_known else "unknown"
    if not fw_ver.strip():
        fw_ver = "unknown"

    wifi_mode = choose_from("Wi-Fi security mode:", ["WPA3", "WPA2", "WPA/WPA2 mixed", "WEP", "Open/None", "Unknown"])
    wps_enabled = yes_no("Is WPS enabled?")
    upnp_enabled = yes_no("Is UPnP enabled?")
    remote_admin = yes_no("Is remote administration enabled (manage router from the internet)?")
    guest_net = yes_no("Is a guest Wi-Fi network enabled?")
    iot_isolated = yes_no("Are IoT devices isolated/segmented from main devices (separate VLAN/SSID or client isolation)?")
    dns_filter = choose_from("DNS filtering in use:", ["None", "Router DNS filtering", "Pi-hole/AdGuard", "NextDNS", "Other/Unknown"])
    pass_strength = choose_from("Router admin password strength:", ["Unique strong", "Okay but reused", "Weak/default/suspected", "Unknown"])
    port_fw = yes_no("Any port forwards configured?")
    exposed_services = choose_yes_no_unknown("Any services exposed to the internet (WAN) that you know of?")

    device_count = safe_input("Approx number of devices on network (rough): ").strip() or "unknown"

    affected = f"Home Router {router_make} ({router_ip})"

    # Firmware unknown
    if fw_ver.strip().lower() in ("unknown", ""):
        add_finding_auto(
            data,
            "Router Firmware Version Unknown / Not Verified",
            affected,
            "Router firmware version was not confirmed during the audit, which makes it harder to assess exposure to known security issues.",
            "Informational", "Medium",
            f"Firmware version reported: {fw_ver}",
            "Unpatched firmware is a common root cause of router compromise and persistent network exposure.",
            "Check firmware version in admin UI; update to latest stable release from vendor; enable auto-update if supported."
        )

    # Wi-Fi mode
    if wifi_mode in ("Open/None", "WEP"):
        add_finding_auto(
            data,
            f"Insecure Wi-Fi Encryption Mode ({wifi_mode})",
            f"Wi-Fi Network (via {router_make})",
            f"Wireless encryption is configured as {wifi_mode}, which is not considered secure.",
            "High", "High",
            f"Wi-Fi mode selected: {wifi_mode}",
            "Attackers nearby can intercept traffic, join the network, and access internal devices.",
            "Switch to WPA3 (preferred) or WPA2-AES; disable legacy modes; rotate Wi-Fi password."
        )
    elif wifi_mode in ("WPA/WPA2 mixed", "Unknown"):
        add_finding_auto(
            data,
            f"Weak/Unverified Wi-Fi Security Mode ({wifi_mode})",
            f"Wi-Fi Network (via {router_make})",
            f"Wi-Fi security mode is {wifi_mode}. Mixed/unknown modes can allow weaker fallback behavior.",
            "Medium", "Medium",
            f"Wi-Fi mode selected: {wifi_mode}",
            "Increases risk of downgrade/legacy compatibility weaknesses and unauthorized access attempts.",
            "Set Wi-Fi to WPA3 if available; otherwise WPA2-AES only; disable legacy compatibility options."
        )

    # WPS
    if wps_enabled:
        add_finding_auto(
            data,
            "WPS Enabled",
            affected,
            "Wi-Fi Protected Setup (WPS) is enabled. WPS can increase the risk of unauthorized Wi-Fi access depending on router behavior and configuration.",
            "Medium", "Medium",
            "WPS reported enabled",
            "Increases chance of unauthorized access to the wireless network, which can lead to internal device compromise.",
            "Disable WPS; rely on strong WPA2/WPA3 passphrase; rotate Wi-Fi password after change."
        )

    # UPnP
    if upnp_enabled:
        add_finding_auto(
            data,
            "UPnP Enabled on Router",
            affected,
            "UPnP is enabled. UPnP allows devices to request port mappings automatically, which can unintentionally expose internal services to the internet.",
            "Medium", "Medium",
            "UPnP reported enabled",
            "Increases risk of internal devices being exposed externally without explicit review, enabling remote compromise pathways.",
            "Disable UPnP; create explicit port forwards only when necessary; periodically review WAN exposure."
        )

    # Remote admin
    if remote_admin:
        add_finding_auto(
            data,
            "Remote Administration Enabled",
            affected,
            "Remote administration is enabled, allowing router management from the internet. This increases exposure to credential attacks and router CVEs.",
            "High", "Medium",
            "Remote admin reported enabled",
            "Attackers can target the router login remotely; compromise can grant persistent control of the home network.",
            "Disable remote admin; if required, restrict to VPN-only access; enforce strong unique admin password and MFA if supported."
        )

    # Admin password strength
    if pass_strength in ("Weak/default/suspected", "Okay but reused", "Unknown"):
        imp = "High" if pass_strength == "Weak/default/suspected" else "Medium"
        lik = "High" if pass_strength == "Weak/default/suspected" else "Medium"
        add_finding_auto(
            data,
            f"Router Admin Credential Risk ({pass_strength})",
            affected,
            f"Router admin password was assessed as '{pass_strength}'. Weak, reused, or unverified admin credentials increase compromise risk.",
            imp, lik,
            f"Password strength selected: {pass_strength}",
            "Compromised router credentials can lead to DNS hijacking, traffic interception, and persistent access to the network.",
            "Set a unique strong admin password (password manager); enable MFA if available; disable admin access from Wi-Fi guest networks."
        )

    # Guest network missing
    if not guest_net:
        add_finding_auto(
            data,
            "Guest Network Not Enabled",
            f"Wi-Fi Network (via {router_make})",
            "Guest Wi-Fi is not enabled. Without a guest network, visitors often share the main network, increasing exposure of personal devices and IoT assets.",
            "Low", "Medium",
            "Guest network reported disabled",
            "Visitors’ devices may introduce malware or insecure services into the same network as sensitive devices.",
            "Enable guest Wi-Fi; isolate guests from LAN; use strong password; rotate periodically."
        )

    # IoT segmentation
    if not iot_isolated:
        add_finding_auto(
            data,
            "IoT Devices Not Segmented/Isolated",
            "Home Network",
            "IoT devices are not isolated from main devices. IoT devices commonly have weaker security and can become pivot points.",
            "Medium", "Medium",
            "IoT isolation reported: No",
            "Compromise of one IoT device can enable lateral movement to personal computers, NAS devices, and phones.",
            "Create separate IoT SSID/VLAN; block IoT → LAN by default; allow only required outbound access."
        )

    # DNS filtering
    if dns_filter == "None":
        add_finding_auto(
            data,
            "No DNS Filtering / Blocking in Place",
            "Home Network",
            "No DNS filtering is configured. DNS filtering can reduce exposure to known malicious domains and phishing infrastructure.",
            "Low", "Medium",
            "DNS filtering selected: None",
            "Increases likelihood of successful phishing/malware callbacks and ad/tracker exposure.",
            "Consider NextDNS / Pi-hole / router DNS filtering; enable blocklists; enforce on all clients where possible."
        )

    # Port forwards / WAN exposure
    if port_fw:
        add_finding_auto(
            data,
            "Port Forwards Present (Review Needed)",
            affected,
            "Port forwards are configured. Port forwards can expose internal services externally and should be reviewed for necessity and secure configuration.",
            "Medium", "Medium",
            "Port forwards reported: Yes",
            "Exposed internal services increase the likelihood of remote compromise if services are unpatched or weakly authenticated.",
            "List current port forwards; remove unused; restrict source IPs if possible; prefer VPN for remote access."
        )

    if exposed_services == "Yes":
        add_finding_auto(
            data,
            "Known Services Exposed to Internet (WAN)",
            "Home Network Perimeter",
            "One or more services are known to be exposed to the internet. Any exposed service should be assessed for patching, authentication, and necessity.",
            "High", "Medium",
            "WAN exposure reported: Yes",
            "Internet-exposed services are frequently targeted and can lead to full network compromise if vulnerable.",
            "Minimize exposure; keep services patched; enforce strong auth; consider VPN-only access; monitor logs."
        )
    elif exposed_services == "Unknown":
        add_finding_auto(
            data,
            "Internet Exposure Not Verified",
            "Home Network Perimeter",
            "External (WAN) exposure was not verified during the audit. Verifying WAN exposure reduces blind spots.",
            "Informational", "Medium",
            "WAN exposure reported: Unknown",
            "Unverified exposure can hide unnecessary open services that attackers routinely scan for.",
            "Perform an external exposure review (ISP modem/router, port forwards, UPnP); document any exposed ports/services."
        )

    # Phase auto-updates (keeps methodology realistic)
    phases = get_phase_state(data)
    phases["Pre-Engagement"]["status"] = "complete"
    phases["Pre-Engagement"]["updated_utc"] = now_iso()

    for ph in ("Reconnaissance", "Scanning", "Enumeration", "Vulnerability Analysis", "Reporting"):
        if phases.get(ph, {}).get("status") == "not_started":
            phases[ph]["status"] = "in_progress"
            phases[ph]["updated_utc"] = now_iso()

    # Summary note
    note = (
        f"Home audit completed. Router={router_make} ({router_ip}), FW={fw_ver}, "
        f"WiFi={wifi_mode}, Devices~{device_count}, DNS={dns_filter}."
    )
    data.setdefault("work", {}).setdefault("notes", []).append({"ts_utc": now_iso(), "text": note})

    save_engagement(p, data)
    print("\nHome audit complete. Findings were added automatically.")
    print("Next: python3 bhd.py finding list | python3 bhd.py report")


# --------------------------
# Report
# --------------------------
def cmd_report(_args):
    p = pick_current_engagement()
    data = load_engagement(p)

    meta = data.get("meta", {})
    scope = data.get("scope", {})
    phases = get_phase_state(data)
    work = data.get("work", {})
    findings = work.get("findings", [])
    notes = work.get("notes", [])

    # Sort findings by numeric ID ascending for deterministic output
    findings = sorted(findings, key=finding_sort_key)

    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    for f in findings:
        sev = f.get("severity", "Medium")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    report = []
    report.append(f"# Penetration Test Report — {meta.get('client','')}")
    report.append("")
    report.append(f"**Project:** {meta.get('project','')}")
    report.append(f"**Test Type:** {meta.get('test_type','')}")
    report.append(f"**Created (UTC):** {meta.get('created_utc','')}")
    report.append("")

    report.append("## Executive Summary")
    report.append("")
    report.append(
        f"This assessment identified **{len(findings)}** total findings. "
        f"Severity breakdown: "
        f"Critical {sev_counts.get('Critical',0)}, "
        f"High {sev_counts.get('High',0)}, "
        f"Medium {sev_counts.get('Medium',0)}, "
        f"Low {sev_counts.get('Low',0)}, "
        f"Informational {sev_counts.get('Informational',0)}."
    )
    report.append("")

    report.append("## Scope")
    report.append("")
    report.append("### In-Scope Targets")
    for t in scope.get("in_scope", []):
        report.append(f"- {t}")
    if scope.get("out_of_scope"):
        report.append("")
        report.append("### Out of Scope")
        report.append(f"- {scope.get('out_of_scope')}")
    if scope.get("rules_of_engagement"):
        report.append("")
        report.append("### Rules of Engagement")
        report.append(scope.get("rules_of_engagement"))

    report.append("")
    report.append("## Methodology")
    report.append("")
    report.append("The engagement followed a phased methodology. Phase status at the time of reporting:")
    report.append("")
    for name, why in PHASES:
        st = phases.get(name, {}).get("status", "not_started")
        report.append(f"- **{name}** — {st}  \n  _{why}_")
        pnotes = phases.get(name, {}).get("notes", [])
        for n in pnotes:
            report.append(f"  - {n.get('ts_utc','')}: {n.get('text','')}")
    report.append("")

    report.append("## Findings Summary")
    report.append("")
    if not findings:
        report.append("_No findings were recorded._")
    else:
        report.append("| ID | Severity | Priority | Title | Affected Target |")
        report.append("|---|---|---|---|---|")
        for f in findings:
            report.append(
                f"| {f.get('id','')} | {f.get('severity','')} | {f.get('remediation_priority','')} | "
                f"{f.get('title','')} | {f.get('affected_target','')} |"
            )
    report.append("")

    report.append("## Detailed Findings")
    report.append("")
    if not findings:
        report.append("_No detailed findings._")
    else:
        for f in findings:
            report.append(f"### {f.get('id','')} — {f.get('title','Untitled')}")
            report.append("")
            report.append(f"- **Severity:** {f.get('severity','')}")
            report.append(f"- **Impact Level:** {f.get('impact_level','')}")
            report.append(f"- **Likelihood:** {f.get('likelihood','')}")
            report.append(f"- **Remediation Priority:** {f.get('remediation_priority','')}")
            report.append(f"- **Affected Target:** {f.get('affected_target','')}")
            if f.get("auto_generated"):
                report.append(f"- **Auto-Generated:** Yes")
            report.append("")
            report.append("**Description**")
            report.append(f.get("description", ""))
            report.append("")
            report.append("**Evidence**")
            report.append(f.get("evidence", ""))
            report.append("")
            report.append("**Business Impact**")
            report.append(f.get("business_impact", ""))
            report.append("")
            report.append("**Recommendation**")
            report.append(f.get("recommendation", ""))
            report.append("")

    report.append("## Engagement Notes")
    report.append("")
    if not notes:
        report.append("_No general notes were recorded._")
    else:
        for n in notes:
            report.append(f"- **{n.get('ts_utc','')}** — {n.get('text','')}")

    out = p / "report.md"
    out.write_text("\n".join(report))
    print(f"Generated report: {out}")


# --------------------------
# CLI Parser
# --------------------------
def build_parser():
    parser = argparse.ArgumentParser(prog="bhd", description="Black Hat Defense CLI (Guardrails + Home Audit)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Engagements group
    p_eng = sub.add_parser("engagements", help="Manage engagements")
    eng_sub = p_eng.add_subparsers(dest="eng_cmd", required=True)

    eng_sub.add_parser("list", help="List all engagements").set_defaults(func=cmd_engagements_list)

    p_eswitch = eng_sub.add_parser("switch", help="Switch to a different engagement")
    p_eswitch.add_argument("name", help="Engagement folder name")
    p_eswitch.set_defaults(func=cmd_engagements_switch)

    sub.add_parser("init", help="Create and select a new engagement").set_defaults(func=cmd_init)
    sub.add_parser("show", help="Show current engagement summary").set_defaults(func=cmd_show)

    p_add = sub.add_parser("add-target", help="Add an in-scope target")
    p_add.add_argument("target", help="IP / domain / hostname")
    p_add.set_defaults(func=cmd_add_target)

    p_note = sub.add_parser("note", help="Add a general note to the current engagement")
    p_note.add_argument("text", help="Note text")
    p_note.set_defaults(func=cmd_note)

    # Phase group
    p_phase = sub.add_parser("phase", help="Phase status and updates")
    phase_sub = p_phase.add_subparsers(dest="phase_cmd", required=True)

    phase_sub.add_parser("status", help="Show phase status with coaching").set_defaults(func=cmd_phase_status)

    p_pset = phase_sub.add_parser("set", help="Set a phase status")
    p_pset.add_argument("phase", help="Phase name (use phase status to copy exact name)")
    p_pset.add_argument("status", help="not_started | in_progress | complete")
    p_pset.set_defaults(func=cmd_phase_set)

    p_pnote = phase_sub.add_parser("note", help="Add a note to a phase")
    p_pnote.add_argument("phase", help="Phase name (use phase status to copy exact name)")
    p_pnote.add_argument("text", help="Note text")
    p_pnote.set_defaults(func=cmd_phase_note)

    # Finding group
    p_find = sub.add_parser("finding", help="Manage findings")
    find_sub = p_find.add_subparsers(dest="finding_cmd", required=True)

    find_sub.add_parser("add", help="Add a finding (guided + validated)").set_defaults(func=cmd_finding_add)
    find_sub.add_parser("list", help="List findings").set_defaults(func=cmd_finding_list)

    p_fshow = find_sub.add_parser("show", help="Show detailed finding information")
    p_fshow.add_argument("id", help="Finding ID (e.g., F-001)")
    p_fshow.set_defaults(func=cmd_finding_show)

    p_fedit = find_sub.add_parser("edit", help="Edit a finding")
    p_fedit.add_argument("id", help="Finding ID (e.g., F-001)")
    p_fedit.set_defaults(func=cmd_finding_edit)

    p_fdel = find_sub.add_parser("delete", help="Delete a finding")
    p_fdel.add_argument("id", help="Finding ID (e.g., F-001)")
    p_fdel.set_defaults(func=cmd_finding_delete)

    p_fstatus = find_sub.add_parser("status", help="Update finding status")
    p_fstatus.add_argument("id", help="Finding ID (e.g., F-001)")
    p_fstatus.add_argument("status", choices=["open", "remediated", "accepted", "retest"], help="New status")
    p_fstatus.set_defaults(func=cmd_finding_status)

    p_ffilter = find_sub.add_parser("filter", help="Filter findings")
    p_ffilter.add_argument("--severity", choices=["Critical", "High", "Medium", "Low", "Informational"])
    p_ffilter.add_argument("--target", help="Filter by affected target (substring match)")
    p_ffilter.add_argument("--status", choices=["open", "remediated", "accepted", "retest"])
    p_ffilter.set_defaults(func=cmd_finding_filter)

    p_fsearch = find_sub.add_parser("search", help="Search findings by keyword")
    p_fsearch.add_argument("query", help="Search term")
    p_fsearch.set_defaults(func=cmd_finding_search)

    # Home audit group
    p_home = sub.add_parser("home-audit", help="Run a home security audit questionnaire")
    home_sub = p_home.add_subparsers(dest="home_cmd", required=True)
    home_sub.add_parser("run", help="Run home audit wizard and auto-create findings").set_defaults(func=cmd_home_audit_run)

    sub.add_parser("report", help="Generate report.md for the current engagement").set_defaults(func=cmd_report)

    return parser


def main():
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
