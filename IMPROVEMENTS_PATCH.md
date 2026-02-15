# Critical Improvements Implementation Guide

## Quick Wins to Add (Copy/Paste Ready)

### 1. Add Finding Delete Command

Add this function after `cmd_finding_list`:

```python
def cmd_finding_delete(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    finding_id = args.id
    # Find the finding
    found = None
    for f in findings:
        if f.get("id") == finding_id:
            found = f
            break

    if not found:
        print(f"Finding {finding_id} not found.", file=sys.stderr)
        sys.exit(1)

    # Confirm deletion
    print(f"About to delete: {found['id']} - {found['title']}")
    if not yes_no("Are you sure?"):
        print("Canceled.")
        return

    # Remove it
    data["work"]["findings"] = [f for f in findings if f.get("id") != finding_id]
    save_engagement(p, data)
    print(f"Deleted finding {finding_id}")
```

Add to parser (in `build_parser`, in the finding section):

```python
p_fdel = find_sub.add_parser("delete", help="Delete a finding")
p_fdel.add_argument("id", help="Finding ID (e.g., F-001)")
p_fdel.set_defaults(func=cmd_finding_delete)
```

### 2. Add Finding Edit Command (Simple Version)

Add this function after `cmd_finding_delete`:

```python
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
    title = safe_input(f"Title [{found['title']}]: ").strip() or found['title']
    affected = safe_input(f"Affected [{found['affected_target']}]: ").strip() or found['affected_target']
    description = safe_input(f"Description [{found['description'][:50]}...]: ").strip() or found['description']

    # Only update if changed
    found['title'] = title
    found['affected_target'] = affected
    found['description'] = description

    findings[found_idx] = found
    data["work"]["findings"] = findings
    save_engagement(p, data)
    print(f"Updated finding {finding_id}")
```

Add to parser:

```python
p_fedit = find_sub.add_parser("edit", help="Edit a finding")
p_fedit.add_argument("id", help="Finding ID (e.g., F-001)")
p_fedit.set_defaults(func=cmd_finding_edit)
```

### 3. Add Engagements List Command

Add this function before `cmd_init`:

```python
def cmd_engagements_list(_args):
    ensure_dirs()
    if not list(ENG_DIR.iterdir()):
        print("No engagements yet. Run: python3 bhd.py init")
        return

    current = ""
    if CURRENT_FILE.exists():
        current = CURRENT_FILE.read_text().strip()

    print("=== Engagements ===")
    for eng_dir in sorted(ENG_DIR.iterdir()):
        if not eng_dir.is_dir():
            continue
        marker = " ← CURRENT" if eng_dir.name == current else ""
        data = load_engagement(eng_dir)
        meta = data.get("meta", {})
        findings_count = len(data.get("work", {}).get("findings", []))
        print(f"\n{eng_dir.name}{marker}")
        print(f"  Client: {meta.get('client', 'N/A')}")
        print(f"  Project: {meta.get('project', 'N/A')}")
        print(f"  Type: {meta.get('test_type', 'N/A')}")
        print(f"  Findings: {findings_count}")
```

### 4. Add Engagements Switch Command

Add this function after `cmd_engagements_list`:

```python
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
```

Add to parser (new engagements subcommand):

```python
# Engagements group
p_eng = sub.add_parser("engagements", help="Manage engagements")
eng_sub = p_eng.add_subparsers(dest="eng_cmd", required=True)

eng_sub.add_parser("list", help="List all engagements").set_defaults(func=cmd_engagements_list)

p_eswitch = eng_sub.add_parser("switch", help="Switch to a different engagement")
p_eswitch.add_argument("name", help="Engagement folder name")
p_eswitch.set_defaults(func=cmd_engagements_switch)
```

### 5. Add Finding Filter Command

Add this function after `cmd_finding_list`:

```python
def cmd_finding_filter(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    filtered = findings

    if args.severity:
        filtered = [f for f in filtered if f.get("severity") == args.severity]

    if args.target:
        filtered = [f for f in filtered if args.target in f.get("affected_target", "")]

    if args.status:
        filtered = [f for f in filtered if f.get("status") == args.status]

    if not filtered:
        print("No findings match your filters.")
        return

    print(f"=== Findings (filtered: {len(filtered)} of {len(findings)}) ===")
    for f in filtered:
        auto = " [AUTO]" if f.get("auto_generated") else ""
        print(f"- {f.get('id')} [{f.get('severity')}] {f.get('title')}{auto}")
        print(f"  Target: {f.get('affected_target')}")
```

Add to parser:

```python
p_ffilter = find_sub.add_parser("filter", help="Filter findings")
p_ffilter.add_argument("--severity", choices=["Critical", "High", "Medium", "Low", "Informational"])
p_ffilter.add_argument("--target", help="Filter by affected target (substring match)")
p_ffilter.add_argument("--status", choices=["open", "remediated", "accepted"])
p_ffilter.set_defaults(func=cmd_finding_filter)
```

### 6. Add Color Output (Optional but Nice)

Add at top of file after imports:

```python
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    Fore = Style = type('', (), {'__getattr__': lambda *_: ''})()
```

Add helper function:

```python
def colored_severity(severity: str) -> str:
    if not COLORS_AVAILABLE:
        return severity
    colors = {
        "Critical": Fore.RED,
        "High": Fore.RED,
        "Medium": Fore.YELLOW,
        "Low": Fore.BLUE,
        "Informational": Fore.CYAN,
    }
    color = colors.get(severity, "")
    return f"{color}{severity}{Style.RESET_ALL}"
```

Update `cmd_finding_list` to use colors:

```python
def cmd_finding_list(_args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    if not findings:
        print("No findings yet.")
        return

    print("=== Findings ===")
    for f in findings:
        sev = colored_severity(f.get('severity', 'Medium'))
        auto = f" {Fore.CYAN}[AUTO]{Style.RESET_ALL}" if f.get("auto_generated") else ""
        print(f"- {f.get('id')} [{sev}] {f.get('title')}{auto}")
        print(f"  Target: {Fore.WHITE}{f.get('affected_target')}{Style.RESET_ALL}")
```

### 7. Add Finding Search Command

Add this function:

```python
def cmd_finding_search(args):
    p = pick_current_engagement()
    data = load_engagement(p)
    findings = data.get("work", {}).get("findings", [])

    query = args.query.lower()
    matched = []

    for f in findings:
        # Search in title, description, evidence, recommendation
        searchable = " ".join([
            f.get("title", ""),
            f.get("description", ""),
            f.get("evidence", ""),
            f.get("recommendation", ""),
            f.get("affected_target", ""),
        ]).lower()

        if query in searchable:
            matched.append(f)

    if not matched:
        print(f"No findings match '{args.query}'")
        return

    print(f"=== Search Results: '{args.query}' ({len(matched)} found) ===")
    for f in matched:
        print(f"\n{f.get('id')} [{colored_severity(f.get('severity'))}] {f.get('title')}")
        print(f"  Target: {f.get('affected_target')}")
        # Show snippet of where match was found
        desc_snippet = f.get('description', '')[:100]
        print(f"  Description: {desc_snippet}...")
```

Add to parser:

```python
p_fsearch = find_sub.add_parser("search", help="Search findings by keyword")
p_fsearch.add_argument("query", help="Search term")
p_fsearch.set_defaults(func=cmd_finding_search)
```

---

## Updated Help Output

After adding these features, your help will look like:

```
$ python3 bhd.py --help

positional arguments:
  {init,show,add-target,note,phase,finding,home-audit,report,engagements}
    init                Create and select a new engagement
    show                Show current engagement summary
    add-target          Add an in-scope target
    note                Add a general note to the current engagement
    phase               Phase status and updates
    finding             Manage findings
    home-audit          Run a home security audit questionnaire
    report              Generate report.md for the current engagement
    engagements         Manage engagements

$ python3 bhd.py finding --help

positional arguments:
  {add,list,edit,delete,filter,search}
    add                 Add a finding (guided + validated)
    list                List findings
    edit                Edit a finding
    delete              Delete a finding
    filter              Filter findings
    search              Search findings by keyword

$ python3 bhd.py engagements --help

positional arguments:
  {list,switch}
    list                List all engagements
    switch              Switch to a different engagement
```

---

## Installation of Optional Dependencies

For color output:
```bash
pip install colorama
```

For future rich output (progress bars, better tables):
```bash
pip install rich
```

For future interactive prompts:
```bash
pip install questionary
```

---

## Testing Your New Features

### Test Finding Delete:
```bash
python3 bhd.py finding list
python3 bhd.py finding delete F-019
python3 bhd.py finding list  # Verify it's gone
```

### Test Finding Edit:
```bash
python3 bhd.py finding edit F-020
# Enter new values or press Enter to keep current
```

### Test Finding Filter:
```bash
python3 bhd.py finding filter --severity Medium
python3 bhd.py finding filter --target "10.168.168.1"
python3 bhd.py finding filter --severity High --target router
```

### Test Finding Search:
```bash
python3 bhd.py finding search "password"
python3 bhd.py finding search "admin"
python3 bhd.py finding search "UPnP"
```

### Test Engagements Management:
```bash
python3 bhd.py engagements list
python3 bhd.py engagements switch tms-test3-home-test-20260215-065244
python3 bhd.py show  # Verify you switched
```

---

## Next Steps After These Quick Wins

Once these are working well, tackle:

1. **Nmap integration** - Auto-parse nmap XML and create findings
2. **PDF export** - Use reportlab or weasyprint to generate PDFs
3. **Evidence attachments** - Copy files into engagement folder, link from findings
4. **Finding status tracking** - Add "remediated", "verified", "accepted risk" statuses
5. **Better interactive mode** - Use questionary for better prompts

This should significantly improve usability! 🚀
