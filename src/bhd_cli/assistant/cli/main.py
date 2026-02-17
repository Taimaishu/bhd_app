"""Main CLI entrypoint for bhd-assist."""
import argparse
import json
import sys
from pathlib import Path

from ..core.entities import AssistanceLevel
from ..playbooks.loader import PlaybookLoader
from ..policy.guard import PolicyGuard


def cmd_init(args):
    """Initialize bhd-assist workspace."""
    workspace_dir = Path(args.workspace or ".")
    assist_dir = workspace_dir / ".bhd-assist"
    assist_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "workspace": str(workspace_dir.absolute()),
        "assistance_level": 0,
        "version": "0.1.0"
    }

    config_file = assist_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)

    print(json.dumps({
        "status": "initialized",
        "workspace": str(workspace_dir.absolute()),
        "config_file": str(config_file),
        "assistance_level": "VALIDATION_ONLY"
    }, indent=2, sort_keys=True))


def cmd_ingest(args):
    """Ingest tool output and create observations."""
    from ..adapters.parsers.nmap_parser import NmapParser
    from ..adapters.storage.json_store import JSONStorageAdapter

    tool = args.tool or "nmap"
    file_path = args.file

    if not file_path:
        print(json.dumps({
            "status": "error",
            "message": "File path required for ingest"
        }, indent=2, sort_keys=True))
        return

    # Get workspace directory
    workspace_dir = Path(args.workspace or ".")
    storage_dir = workspace_dir / ".bhd-assist" / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Initialize parser and storage
    if tool.lower() == "nmap":
        parser = NmapParser()
    else:
        print(json.dumps({
            "status": "error",
            "message": f"Unsupported tool: {tool}. Only 'nmap' is currently supported."
        }, indent=2, sort_keys=True))
        return

    storage = JSONStorageAdapter(storage_dir)

    try:
        # Parse file
        observations = parser.parse_file(file_path)

        # Save observations
        saved_ids = []
        for obs in observations:
            obs_id = storage.save_observation(obs)
            saved_ids.append(obs_id)

        print(json.dumps({
            "status": "ingested",
            "tool": tool,
            "file": file_path,
            "observations_created": len(observations),
            "observation_ids": saved_ids,
            "storage_path": str(storage_dir)
        }, indent=2, sort_keys=True))

    except FileNotFoundError as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }, indent=2, sort_keys=True))
    except ValueError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Parse error: {e}"
        }, indent=2, sort_keys=True))


def cmd_playbook_list(args):
    """List available playbooks."""
    # Get playbooks directory
    playbooks_dir = Path(__file__).parent.parent / "playbooks" / "library"
    schemas_dir = Path(__file__).parent.parent / "playbooks" / "schemas"

    loader = PlaybookLoader(playbooks_dir, schemas_dir)

    filters = {}
    if args.test_type:
        filters["test_type"] = args.test_type

    playbooks = loader.list_playbooks(filters)

    print(json.dumps({
        "playbooks": playbooks,
        "count": len(playbooks)
    }, indent=2, sort_keys=True))


def cmd_playbook_select(args):
    """Select playbook (stub)."""
    print(json.dumps({
        "status": "selected",
        "playbook_id": args.playbook_id or "auto",
        "message": "Playbook selection stub"
    }, indent=2, sort_keys=True))


def cmd_playbook_render(args):
    """Render playbook as checklist or evidence plan."""
    playbooks_dir = Path(__file__).parent.parent / "playbooks" / "library"
    schemas_dir = Path(__file__).parent.parent / "playbooks" / "schemas"

    loader = PlaybookLoader(playbooks_dir, schemas_dir)

    try:
        playbook_data = loader.load_playbook(args.playbook_id)

        if args.format == "checklist":
            output = loader.render_checklist(playbook_data)
            print(output)
        elif args.format == "evidence":
            evidence_plan = loader.create_evidence_plan(playbook_data)
            print(json.dumps(evidence_plan.to_dict(), indent=2, sort_keys=True))
        elif args.format == "finding":
            # Stub: would need evidence refs
            finding_draft = loader.create_finding_draft(
                playbook_data,
                affected_asset=args.asset or "target_system",
                evidence_refs=[]
            )
            print(json.dumps(finding_draft.to_dict(), indent=2, sort_keys=True))
        else:
            print(json.dumps({"error": f"Unknown format: {args.format}"}, indent=2))
            sys.exit(1)

    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


def cmd_suggest_playbooks(args):
    """Suggest playbooks based on stored observations."""
    from ..adapters.storage.json_store import JSONStorageAdapter
    from ..playbooks.selector import PlaybookSelector

    # Get workspace directory
    workspace_dir = Path(args.workspace or ".")
    storage_dir = workspace_dir / ".bhd-assist" / "storage"

    if not storage_dir.exists():
        print(json.dumps({
            "status": "error",
            "message": "No observations found. Run 'bhd-assist ingest' first."
        }, indent=2, sort_keys=True))
        return

    # Load observations
    storage = JSONStorageAdapter(storage_dir)
    observations = storage.load_observations(session_id="default")

    if not observations:
        print(json.dumps({
            "status": "no_observations",
            "message": "No observations found in storage. Ingest tool output first.",
            "observations_count": 0
        }, indent=2, sort_keys=True))
        return

    # Run selector
    rules_path = Path(__file__).parent.parent / "playbooks" / "selectors" / "selector_rules.yaml"
    selector = PlaybookSelector(rules_path)

    test_type = args.test_type or "network"
    selected_playbook = selector.select_playbook(observations, test_type)

    print(json.dumps({
        "status": "success",
        "test_type": test_type,
        "observations_count": len(observations),
        "selected_playbook": selected_playbook,
        "message": f"Selected playbook: {selected_playbook}" if selected_playbook else "No matching playbook found"
    }, indent=2, sort_keys=True))


def cmd_export(args):
    """Export finding drafts (stub)."""
    print(json.dumps({
        "status": "exported",
        "output_file": args.output or "findings_export.json",
        "format": "bhd-cli",
        "findings_count": 0,
        "message": "Export stub - no drafts to export"
    }, indent=2, sort_keys=True))


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="bhd-assist",
        description="AI-Powered Penetration Testing Assistant (Documentation-centric)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    p_init = subparsers.add_parser("init", help="Initialize bhd-assist workspace")
    p_init.add_argument("--workspace", help="Workspace directory", default=".")
    p_init.set_defaults(func=cmd_init)

    # ingest command
    p_ingest = subparsers.add_parser("ingest", help="Ingest tool output")
    p_ingest.add_argument("--tool", help="Tool name (nmap, burp, etc.)", default="nmap")
    p_ingest.add_argument("--file", help="Input file", required=True)
    p_ingest.add_argument("--workspace", help="Workspace directory", default=".")
    p_ingest.set_defaults(func=cmd_ingest)

    # playbook list command
    p_pb_list = subparsers.add_parser("playbook-list", help="List available playbooks")
    p_pb_list.add_argument("--test-type", help="Filter by test type")
    p_pb_list.set_defaults(func=cmd_playbook_list)

    # playbook select command
    p_pb_select = subparsers.add_parser("playbook-select", help="Select playbook")
    p_pb_select.add_argument("--playbook-id", help="Playbook ID")
    p_pb_select.set_defaults(func=cmd_playbook_select)

    # playbook render command
    p_pb_render = subparsers.add_parser("playbook-render", help="Render playbook")
    p_pb_render.add_argument("playbook_id", help="Playbook ID")
    p_pb_render.add_argument(
        "--format",
        choices=["checklist", "evidence", "finding"],
        default="checklist",
        help="Output format"
    )
    p_pb_render.add_argument("--asset", help="Affected asset (for finding format)")
    p_pb_render.set_defaults(func=cmd_playbook_render)

    # suggest-playbooks command
    p_suggest = subparsers.add_parser("suggest-playbooks", help="Suggest playbooks based on observations")
    p_suggest.add_argument("--test-type", help="Test type (web, network, ics, etc.)", default="network")
    p_suggest.add_argument("--workspace", help="Workspace directory", default=".")
    p_suggest.set_defaults(func=cmd_suggest_playbooks)

    # export command
    p_export = subparsers.add_parser("export", help="Export finding drafts")
    p_export.add_argument("--output", help="Output file", default="findings_export.json")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
