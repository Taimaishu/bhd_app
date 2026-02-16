"""Smoke tests for bhd-cli command."""
import json
import subprocess
import sys
from pathlib import Path


def test_help_command():
    """Test that bhd-cli --help works and shows correct usage."""
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"--help failed: {result.stderr}"
    assert "usage: bhd-cli" in result.stdout, "Usage line should show 'bhd-cli'"
    assert "Black Hat Defense CLI" in result.stdout


def test_engagements_list_no_error():
    """Test that engagements list doesn't crash even with no engagements."""
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "engagements", "list"],
        capture_output=True,
        text=True,
        cwd="/tmp",  # Run in tmp to avoid affecting real engagements
    )
    # Should exit 0 even if no engagements exist
    assert result.returncode == 0, f"engagements list failed: {result.stderr}"
    # Should show either engagements or a message about none existing
    assert (
        "=== Engagements ===" in result.stdout
        or "No engagements yet" in result.stdout
    )


def test_version_info():
    """Test that --help shows version-related info."""
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Should have various commands listed
    assert "init" in result.stdout
    assert "finding" in result.stdout
    assert "report" in result.stdout


def test_version_command():
    """Test that version command works and shows correct format."""
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "version"],
        capture_output=True,
        text=True,
        cwd="/tmp",
    )
    assert result.returncode == 0, f"version command failed: {result.stderr}"
    # Should show "bhd-cli X.Y.Z" format
    assert "bhd-cli" in result.stdout
    # Should have version number (1.1.0 or later)
    assert "1." in result.stdout


def test_storage_abstraction():
    """Test that storage layer can be imported and used."""
    # This is a meta-test ensuring storage.py exists and is importable
    try:
        from bhd_cli.storage import storage, JSONStorage
        assert storage is not None
        assert isinstance(storage, JSONStorage)
    except ImportError as e:
        raise AssertionError(f"Failed to import storage layer: {e}")


def test_export_json_single(tmp_path):
    """Test export json for single engagement with relative path output."""
    # Create a test engagement structure
    eng_dir = tmp_path / "engagements"
    eng1_dir = eng_dir / "test-eng1-20260215-000000"
    eng1_dir.mkdir(parents=True)

    # Create minimal engagement.json
    engagement_data = {
        "meta": {"client": "test1", "project": "proj1", "test_type": "home"},
        "scope": {"in_scope": ["192.168.1.1"]},
        "work": {"findings": [], "notes": []},
    }
    (eng1_dir / "engagement.json").write_text(json.dumps(engagement_data, indent=2))

    # Set current engagement
    (eng_dir / ".current").write_text("test-eng1-20260215-000000")

    # Run export json command
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "export", "json"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )

    assert result.returncode == 0, f"export json failed: {result.stderr}"
    assert "Exported engagement to:" in result.stdout
    # Should print relative path, not absolute
    assert "engagements/test-eng1-20260215-000000/export.json" in result.stdout
    assert "/tmp/" not in result.stdout or str(tmp_path) not in result.stdout

    # Verify export.json was created
    export_file = eng1_dir / "export.json"
    assert export_file.exists(), "export.json should exist"

    # Verify export.json has correct structure
    exported = json.loads(export_file.read_text())
    assert "meta" in exported
    assert "scope" in exported
    assert "work" in exported


def test_export_json_all(tmp_path):
    """Test export json --all for multiple engagements."""
    # Create multiple test engagement structures
    eng_dir = tmp_path / "engagements"

    # Create engagement 1
    eng1_dir = eng_dir / "client-a-20260215-000000"
    eng1_dir.mkdir(parents=True)
    engagement1_data = {
        "meta": {"client": "clienta", "project": "proj1", "test_type": "web"},
        "scope": {"in_scope": ["10.0.0.1"]},
        "work": {"findings": [], "notes": []},
    }
    (eng1_dir / "engagement.json").write_text(json.dumps(engagement1_data, indent=2))

    # Create engagement 2
    eng2_dir = eng_dir / "client-b-20260215-000001"
    eng2_dir.mkdir(parents=True)
    engagement2_data = {
        "meta": {"client": "clientb", "project": "proj2", "test_type": "network"},
        "scope": {"in_scope": ["10.0.0.2"]},
        "work": {"findings": [], "notes": []},
    }
    (eng2_dir / "engagement.json").write_text(json.dumps(engagement2_data, indent=2))

    # Set current engagement (should be ignored with --all)
    (eng_dir / ".current").write_text("client-a-20260215-000000")

    # Run export json --all command
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "export", "json", "--all"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )

    assert result.returncode == 0, f"export json --all failed: {result.stderr}"
    assert "Exporting 2 engagement(s)" in result.stdout
    assert "Exported 2 engagement(s) to JSON" in result.stdout

    # Should show both relative paths (deterministic order: alphabetically sorted)
    assert "engagements/client-a-20260215-000000/export.json" in result.stdout
    assert "engagements/client-b-20260215-000001/export.json" in result.stdout

    # Verify both export files were created
    assert (eng1_dir / "export.json").exists()
    assert (eng2_dir / "export.json").exists()

    # Verify exported files have correct structure
    export1 = json.loads((eng1_dir / "export.json").read_text())
    assert export1["meta"]["client"] == "clienta"

    export2 = json.loads((eng2_dir / "export.json").read_text())
    assert export2["meta"]["client"] == "clientb"


def test_export_json_all_empty(tmp_path):
    """Test export json --all with no engagements."""
    # Create empty engagements directory
    eng_dir = tmp_path / "engagements"
    eng_dir.mkdir()

    # Run export json --all command
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "export", "json", "--all"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )

    assert result.returncode == 0, f"export json --all with empty dir should succeed"
    assert "No engagements found" in result.stdout


def test_export_pdf_relative_path(tmp_path):
    """Test that export pdf prints relative paths (if reportlab available)."""
    # Check if reportlab is available
    try:
        import reportlab
    except ImportError:
        # Skip this test if reportlab not installed
        import pytest
        pytest.skip("reportlab not installed, skipping PDF path test")

    # Create a test engagement structure
    eng_dir = tmp_path / "engagements"
    eng1_dir = eng_dir / "test-pdf-20260215-000000"
    eng1_dir.mkdir(parents=True)

    # Create minimal engagement.json
    engagement_data = {
        "meta": {"client": "testpdf", "project": "proj1", "test_type": "home"},
        "scope": {"in_scope": ["192.168.1.1"]},
        "work": {"findings": [], "notes": []},
    }
    (eng1_dir / "engagement.json").write_text(json.dumps(engagement_data, indent=2))

    # Create report.md (required for PDF generation)
    report_content = """# Test Report

## Summary

This is a test report.

- Finding 1
- Finding 2
"""
    (eng1_dir / "report.md").write_text(report_content)

    # Set current engagement
    (eng_dir / ".current").write_text("test-pdf-20260215-000000")

    # Run export pdf command
    result = subprocess.run(
        [sys.executable, "-m", "bhd_cli.cli", "export", "pdf"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )

    assert result.returncode == 0, f"export pdf failed: {result.stderr}"
    assert "Exported report to:" in result.stdout
    # Should print relative path
    assert "engagements/test-pdf-20260215-000000/report.pdf" in result.stdout

    # Verify report.pdf was created
    pdf_file = eng1_dir / "report.pdf"
    assert pdf_file.exists(), "report.pdf should exist"
    assert pdf_file.stat().st_size > 0, "report.pdf should not be empty"
