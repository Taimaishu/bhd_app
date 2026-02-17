"""Nmap XML output parser."""
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Union

from ...core.entities import Observation, ObservationCategory
from ...core.ports import IParserPort


class NmapParser(IParserPort):
    """Parser for Nmap XML output."""

    def can_parse(self, tool_name: str, output: str) -> bool:
        """Check if this parser can handle the given tool output."""
        if tool_name.lower() == "nmap":
            return True
        # Check if output looks like Nmap XML
        return output.strip().startswith("<?xml") and "nmaprun" in output

    def parse(self, tool_name: str, output: str) -> List[Observation]:
        """Parse Nmap XML output into observations.

        Creates one Observation per open port with:
        - category: "port" for open ports
        - category: "service" for identified services with version info
        - Deterministic IDs based on hash(host+port)
        - Confidence scores based on service detection confidence
        """
        observations = []

        try:
            root = ET.fromstring(output)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse Nmap XML: {e}")

        # Get scan metadata
        scan_args = root.get("args", "nmap")
        scan_start = root.get("start", str(int(datetime.utcnow().timestamp())))

        # Artifact ID for source_artifact field
        artifact_id = hashlib.sha256(f"nmap:{scan_start}:{scan_args}".encode()).hexdigest()[:16]

        # Parse each host
        for host in root.findall(".//host"):
            # Get host address
            address_elem = host.find(".//address[@addrtype='ipv4']")
            if address_elem is None:
                address_elem = host.find(".//address[@addrtype='ipv6']")
            if address_elem is None:
                continue

            host_addr = address_elem.get("addr")

            # Get hostname if available
            hostname_elem = host.find(".//hostname")
            hostname = hostname_elem.get("name") if hostname_elem is not None else None

            # Parse each port
            for port in host.findall(".//port"):
                protocol = port.get("protocol", "tcp")
                portid = port.get("portid")

                state_elem = port.find("state")
                if state_elem is None:
                    continue

                state = state_elem.get("state")
                if state != "open":
                    continue  # Only create observations for open ports

                # Generate deterministic ID
                obs_id = hashlib.sha256(f"{host_addr}:{protocol}:{portid}".encode()).hexdigest()[:16]

                # Get service information
                service_elem = port.find("service")
                service_name = None
                service_product = None
                service_version = None
                service_conf = 5  # Default confidence

                if service_elem is not None:
                    service_name = service_elem.get("name")
                    service_product = service_elem.get("product")
                    service_version = service_elem.get("version")
                    service_conf = int(service_elem.get("conf", "5"))

                # Determine category and confidence
                if service_product or service_version:
                    # If we have version info, this is a service observation
                    category = ObservationCategory.SERVICE
                    confidence = service_conf / 10.0  # Convert 0-10 to 0.0-1.0
                    tags = ["service", service_name] if service_name else ["service"]
                else:
                    # Just an open port
                    category = ObservationCategory.PORT
                    confidence = 0.95  # High confidence for open ports
                    tags = ["open", protocol]
                    if service_name:
                        tags.append(service_name)

                # Build observation data
                data = {
                    "host": host_addr,
                    "port": int(portid),
                    "protocol": protocol,
                    "state": state
                }

                if hostname:
                    data["hostname"] = hostname

                if service_name:
                    data["service"] = service_name

                if service_product:
                    data["product"] = service_product

                if service_version:
                    data["version"] = service_version

                # Create observation
                obs = Observation(
                    id=obs_id,
                    source_artifact=artifact_id,
                    category=category,
                    tags=tags,
                    confidence=confidence,
                    data=data
                )

                observations.append(obs)

        return observations

    def parse_file(self, file_path: Union[str, Path]) -> List[Observation]:
        """Parse Nmap XML file into observations."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Nmap file not found: {file_path}")

        with open(path) as f:
            xml_content = f.read()

        return self.parse("nmap", xml_content)
