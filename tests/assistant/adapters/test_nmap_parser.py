"""Tests for Nmap XML parser."""
import pytest

from bhd_cli.assistant.core.entities import ObservationCategory
from bhd_cli.assistant.adapters.parsers.nmap_parser import NmapParser


# Sample Nmap XML output
SAMPLE_NMAP_XML = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -sV -p22,80,443 192.168.1.1" start="1708185600">
<host>
<address addr="192.168.1.1" addrtype="ipv4"/>
<hostnames>
<hostname name="example.com" type="PTR"/>
</hostnames>
<ports>
<port protocol="tcp" portid="22">
<state state="open" reason="syn-ack"/>
<service name="ssh" product="OpenSSH" version="8.2p1" conf="10"/>
</port>
<port protocol="tcp" portid="80">
<state state="open" reason="syn-ack"/>
<service name="http" conf="3"/>
</port>
<port protocol="tcp" portid="443">
<state state="closed" reason="reset"/>
</port>
<port protocol="tcp" portid="8080">
<state state="open" reason="syn-ack"/>
</port>
</ports>
</host>
</nmaprun>
"""


def test_nmap_parser_can_parse():
    """Test that parser recognizes Nmap XML."""
    parser = NmapParser()

    assert parser.can_parse("nmap", SAMPLE_NMAP_XML)
    assert parser.can_parse("Nmap", SAMPLE_NMAP_XML)
    assert parser.can_parse("other_tool", SAMPLE_NMAP_XML)  # Recognizes XML format
    assert not parser.can_parse("other_tool", "not xml content")


def test_nmap_parser_parses_open_ports():
    """Test that parser creates observations for open ports."""
    parser = NmapParser()

    observations = parser.parse("nmap", SAMPLE_NMAP_XML)

    # Should have 3 observations (ports 22, 80, 8080 - port 443 is closed)
    assert len(observations) == 3


def test_nmap_parser_categorizes_service_with_version():
    """Test that parser categorizes ports with version info as SERVICE."""
    parser = NmapParser()

    observations = parser.parse("nmap", SAMPLE_NMAP_XML)

    # Port 22 has product and version, should be SERVICE
    ssh_obs = [obs for obs in observations if obs.data["port"] == 22][0]
    assert ssh_obs.category == ObservationCategory.SERVICE
    assert ssh_obs.data["service"] == "ssh"
    assert ssh_obs.data["product"] == "OpenSSH"
    assert ssh_obs.data["version"] == "8.2p1"
    assert ssh_obs.confidence == 1.0  # conf=10 -> 1.0


def test_nmap_parser_categorizes_port_without_version():
    """Test that parser categorizes ports without version info as PORT."""
    parser = NmapParser()

    observations = parser.parse("nmap", SAMPLE_NMAP_XML)

    # Port 80 has no version info, should be PORT
    http_obs = [obs for obs in observations if obs.data["port"] == 80][0]
    assert http_obs.category == ObservationCategory.PORT
    assert http_obs.data["service"] == "http"
    assert http_obs.confidence == 0.95


def test_nmap_parser_port_without_service():
    """Test that parser handles ports without service detection."""
    parser = NmapParser()

    observations = parser.parse("nmap", SAMPLE_NMAP_XML)

    # Port 8080 has no service info
    unknown_obs = [obs for obs in observations if obs.data["port"] == 8080][0]
    assert unknown_obs.category == ObservationCategory.PORT
    assert "service" not in unknown_obs.data
    assert unknown_obs.confidence == 0.95


def test_nmap_parser_includes_hostname():
    """Test that parser includes hostname when available."""
    parser = NmapParser()

    observations = parser.parse("nmap", SAMPLE_NMAP_XML)

    for obs in observations:
        assert obs.data["hostname"] == "example.com"


def test_nmap_parser_generates_deterministic_ids():
    """Test that parser generates deterministic IDs based on host+port."""
    parser = NmapParser()

    # Parse twice
    observations1 = parser.parse("nmap", SAMPLE_NMAP_XML)
    observations2 = parser.parse("nmap", SAMPLE_NMAP_XML)

    # IDs should be the same
    ids1 = sorted([obs.id for obs in observations1])
    ids2 = sorted([obs.id for obs in observations2])
    assert ids1 == ids2


def test_nmap_parser_creates_correct_tags():
    """Test that parser creates appropriate tags."""
    parser = NmapParser()

    observations = parser.parse("nmap", SAMPLE_NMAP_XML)

    ssh_obs = [obs for obs in observations if obs.data["port"] == 22][0]
    assert "service" in ssh_obs.tags
    assert "ssh" in ssh_obs.tags

    http_obs = [obs for obs in observations if obs.data["port"] == 80][0]
    assert "open" in http_obs.tags
    assert "tcp" in http_obs.tags
    assert "http" in http_obs.tags


def test_nmap_parser_sets_source_artifact():
    """Test that parser sets source_artifact field."""
    parser = NmapParser()

    observations = parser.parse("nmap", SAMPLE_NMAP_XML)

    # All observations should have the same source_artifact
    artifacts = set(obs.source_artifact for obs in observations)
    assert len(artifacts) == 1
    assert len(list(artifacts)[0]) == 16  # 16-char hash


def test_nmap_parser_handles_invalid_xml():
    """Test that parser raises error for invalid XML."""
    parser = NmapParser()

    with pytest.raises(ValueError, match="Failed to parse Nmap XML"):
        parser.parse("nmap", "<invalid>xml</invalid")


def test_nmap_parser_multi_host():
    """Test that parser handles multiple hosts."""
    multi_host_xml = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -p22 192.168.1.1-2" start="1708185600">
<host>
<address addr="192.168.1.1" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="22">
<state state="open" reason="syn-ack"/>
<service name="ssh"/>
</port>
</ports>
</host>
<host>
<address addr="192.168.1.2" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="22">
<state state="open" reason="syn-ack"/>
<service name="ssh"/>
</port>
</ports>
</host>
</nmaprun>
"""

    parser = NmapParser()
    observations = parser.parse("nmap", multi_host_xml)

    # Should have 2 observations (one per host)
    assert len(observations) == 2

    hosts = [obs.data["host"] for obs in observations]
    assert "192.168.1.1" in hosts
    assert "192.168.1.2" in hosts


def test_nmap_parser_rdp_canonicalization():
    """Test that parser canonicalizes RDP service aliases."""
    # Test ms-wbt-server alias
    rdp_xml = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -p3389 10.0.0.1" start="1708185600">
<host>
<address addr="10.0.0.1" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="3389">
<state state="open" reason="syn-ack"/>
<service name="ms-wbt-server" product="Microsoft Terminal Services" version="10.0" conf="10"/>
</port>
</ports>
</host>
</nmaprun>
"""

    parser = NmapParser()
    observations = parser.parse("nmap", rdp_xml)

    assert len(observations) == 1
    obs = observations[0]

    # Should canonicalize to "rdp"
    assert obs.data["service"] == "rdp"
    assert obs.data["service_raw"] == "ms-wbt-server"
    assert obs.data["port"] == 3389
    assert obs.category == ObservationCategory.SERVICE
    assert "rdp" in obs.tags


def test_nmap_parser_vnc_rfb_canonicalization():
    """Test that parser canonicalizes VNC/RFB service aliases."""
    vnc_xml = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -p5900 10.0.0.1" start="1708185600">
<host>
<address addr="10.0.0.1" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="5900">
<state state="open" reason="syn-ack"/>
<service name="rfb" product="RealVNC" version="4.1.2" conf="10"/>
</port>
</ports>
</host>
</nmaprun>
"""

    parser = NmapParser()
    observations = parser.parse("nmap", vnc_xml)

    assert len(observations) == 1
    obs = observations[0]

    # Should canonicalize rfb to "vnc"
    assert obs.data["service"] == "vnc"
    assert obs.data["service_raw"] == "rfb"
    assert obs.data["port"] == 5900
    assert obs.category == ObservationCategory.SERVICE
    assert "vnc" in obs.tags


def test_nmap_parser_product_based_rdp_detection():
    """Test that parser detects RDP from product string even with weird service name."""
    rdp_product_xml = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -p3389 10.0.0.1" start="1708185600">
<host>
<address addr="10.0.0.1" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="3389">
<state state="open" reason="syn-ack"/>
<service name="unknown" product="Microsoft Remote Desktop Services" conf="8"/>
</port>
</ports>
</host>
</nmaprun>
"""

    parser = NmapParser()
    observations = parser.parse("nmap", rdp_product_xml)

    assert len(observations) == 1
    obs = observations[0]

    # Should detect RDP from product string
    assert obs.data["service"] == "rdp"
    assert obs.data["service_raw"] == "unknown"
    assert obs.data["product"] == "Microsoft Remote Desktop Services"


def test_nmap_parser_ssh_unchanged():
    """Test that existing SSH detection still works correctly."""
    ssh_xml = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -p22 10.0.0.1" start="1708185600">
<host>
<address addr="10.0.0.1" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="22">
<state state="open" reason="syn-ack"/>
<service name="ssh" product="OpenSSH" version="8.9p1" conf="10"/>
</port>
</ports>
</host>
</nmaprun>
"""

    parser = NmapParser()
    observations = parser.parse("nmap", ssh_xml)

    assert len(observations) == 1
    obs = observations[0]

    # SSH should remain unchanged (canonical name = raw name)
    assert obs.data["service"] == "ssh"
    assert "service_raw" not in obs.data  # Not stored when same as canonical
    assert obs.data["product"] == "OpenSSH"
    assert obs.data["version"] == "8.9p1"
    assert obs.category == ObservationCategory.SERVICE
    assert "ssh" in obs.tags


def test_nmap_parser_telnet_canonicalization():
    """Test that parser handles telnet correctly."""
    telnet_xml = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -p23 10.0.0.1" start="1708185600">
<host>
<address addr="10.0.0.1" addrtype="ipv4"/>
<ports>
<port protocol="tcp" portid="23">
<state state="open" reason="syn-ack"/>
<service name="telnet" conf="8"/>
</port>
</ports>
</host>
</nmaprun>
"""

    parser = NmapParser()
    observations = parser.parse("nmap", telnet_xml)

    assert len(observations) == 1
    obs = observations[0]

    assert obs.data["service"] == "telnet"
    assert obs.data["port"] == 23
    assert "telnet" in obs.tags
