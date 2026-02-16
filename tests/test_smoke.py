"""Smoke tests for bhd-cli command."""
import subprocess
import sys


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
