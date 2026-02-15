# Penetration Test Report — tms

**Project:** test3-home-test
**Test Type:** home
**Created (UTC):** 2026-02-15T13:52:44Z

## Executive Summary

This assessment identified **5** total findings. Severity breakdown: Critical 0, High 0, Medium 3, Low 2, Informational 0.

## Scope

### In-Scope Targets
- 10.168.168.1

### Rules of Engagement
no Dos. scan for open ports. search for vulnerabilties. test vulnerabilities.

## Methodology

The engagement followed a phased methodology. Phase status at the time of reporting:

- **Pre-Engagement** — complete  
  _Scope, written authorization, and ROE. This protects you legally and keeps work aligned._
- **Reconnaissance** — complete  
  _Passive/active discovery to understand the target surface before touching it harder._
- **Scanning** — complete  
  _Identify open ports/services and basic versions. This is your map of the environment._
- **Enumeration** — complete  
  _Go deeper on discovered services (endpoints, shares, users, configs). This is where findings are born._
- **Vulnerability Analysis** — complete  
  _Translate observed conditions into likely weaknesses and risk hypotheses._
- **Exploitation** — not_started  
  _Only if authorized. Minimal-impact proof. Capture evidence, don’t ‘go wild’._
- **Reporting** — complete  
  _Convert technical results into risk + remediation. This is what clients pay for._

## Findings Summary

| ID | Severity | Priority | Title | Affected Target |
|---|---|---|---|---|
| F-019 | Low | Backlog (90+ days) | nmap_scan | 10,168.168.1 |
| F-020 | Medium | Planned (30–90 days) | Router Admin Credential Risk (Okay but reused) | Home Router Netgear Orbi RBE361 (10.168.168.1) |
| F-021 | Low | Backlog (90+ days) | Guest Network Not Enabled | Wi-Fi Network (via Netgear Orbi RBE361) |
| F-022 | Medium | Planned (30–90 days) | IoT Devices Not Segmented/Isolated | Home Network |
| F-023 | Medium | Planned (30–90 days) | Router Web Administration Interface Accessible on LAN (HTTP/HTTPS) | Home Router Netgear Orbi RBE361 (10.168.168.1) |

## Detailed Findings

### F-019 — nmap_scan

- **Severity:** Low
- **Impact Level:** Low
- **Likelihood:** Medium
- **Remediation Priority:** Backlog (90+ days)
- **Affected Target:** 10,168.168.1

**Description**
I ran nmap -Pn -T4 --top-ports 1000 10.168.168.1 -v and the reults came back with the following open TCP ports; port 53(DNS), port 80(http), port 443(https), and filtered port 6389(clariion-evr01.

**Evidence**
web ui login username is admin and the password is a good password but has been reused in other places. UPnP was eger enabled. web login seems to be only available localy, meaning no remote access. scanned for open ports and foiund 53, 80, and 443 open.

**Business Impact**
Password should be rotated every 90 days.

**Recommendation**
rotate password, and ensure UPnP is deactivated.

### F-020 — Router Admin Credential Risk (Okay but reused)

- **Severity:** Medium
- **Impact Level:** Medium
- **Likelihood:** Medium
- **Remediation Priority:** Planned (30–90 days)
- **Affected Target:** Home Router Netgear Orbi RBE361 (10.168.168.1)
- **Auto-Generated:** Yes

**Description**
Router admin password was assessed as 'Okay but reused'. Weak, reused, or unverified admin credentials increase compromise risk.

**Evidence**
Password strength selected: Okay but reused

**Business Impact**
Compromised router credentials can lead to DNS hijacking, traffic interception, and persistent access to the network.

**Recommendation**
Set a unique strong admin password (password manager); enable MFA if available; disable admin access from Wi-Fi guest networks.

### F-021 — Guest Network Not Enabled

- **Severity:** Low
- **Impact Level:** Low
- **Likelihood:** Medium
- **Remediation Priority:** Backlog (90+ days)
- **Affected Target:** Wi-Fi Network (via Netgear Orbi RBE361)
- **Auto-Generated:** Yes

**Description**
Guest Wi-Fi is not enabled. Without a guest network, visitors often share the main network, increasing exposure of personal devices and IoT assets.

**Evidence**
Guest network reported disabled

**Business Impact**
Visitors’ devices may introduce malware or insecure services into the same network as sensitive devices.

**Recommendation**
Enable guest Wi-Fi; isolate guests from LAN; use strong password; rotate periodically.

### F-022 — IoT Devices Not Segmented/Isolated

- **Severity:** Medium
- **Impact Level:** Medium
- **Likelihood:** Medium
- **Remediation Priority:** Planned (30–90 days)
- **Affected Target:** Home Network
- **Auto-Generated:** Yes

**Description**
IoT devices are not isolated from main devices. IoT devices commonly have weaker security and can become pivot points.

**Evidence**
IoT isolation reported: No

**Business Impact**
Compromise of one IoT device can enable lateral movement to personal computers, NAS devices, and phones.

**Recommendation**
Create separate IoT SSID/VLAN; block IoT → LAN by default; allow only required outbound access.

### F-023 — Router Web Administration Interface Accessible on LAN (HTTP/HTTPS)

- **Severity:** Medium
- **Impact Level:** Medium
- **Likelihood:** Medium
- **Remediation Priority:** Planned (30–90 days)
- **Affected Target:** Home Router Netgear Orbi RBE361 (10.168.168.1)

**Description**
Router admin interface is reachable on the local network over HTTP/HTTPS. If any LAN device is compromised (or a guest joins), this increases the chance of router takeover attempts (password guessing, session hijack, known CVEs, etc.).

**Evidence**
nmap -Pn -T4 --top-ports 1000 10.168.168.1 shows TCP/80 and TCP/443 open; admin UI reachable from LAN; login username observed as “admin”.

**Business Impact**
Router compromise can enable DNS hijacking, traffic interception, device redirection, and persistence across the home network.Recommendation: Restrict admin UI access (LAN-only is ok), disable HTTP if possible (HTTPS only), ensure unique strong admin password + MFA if supported, and limit which devices can reach router admin UI.

**Recommendation**
Router compromise can enable DNS hijacking, traffic interception, device redirection, and persistence across the ht admin UI access (LAN-only is ok), disable HTTP if possible (HTTPS only), ensure unique strong admin password + MFA if supported, and limit which devices can reach router admin UI.

## Engagement Notes

- **2026-02-15T13:59:34Z** — Home audit completed. Router=Netgear Orbi RBE362 (10.168.168.1), FW=unknown, WiFi=Unknown, Devices~7, DNS=Other/Unknown.
- **2026-02-15T14:52:44Z** — Home audit completed. Router=Netgear Orbi RBE362 (10.168.168.1), FW=V12.1.3.11_5.1.12, WiFi=WPA2, Devices~6-10, DNS=Router DNS filtering.
- **2026-02-15T18:42:15Z** — Home audit completed. Router=Netgear Orbi RBE361 (10.168.168.1), FW=V12.1.3.11_5.1.12, WiFi=WPA2, Devices~6-10, DNS=Router DNS filtering.
- **2026-02-15T20:15:51Z** — Home audit completed. Router=Netgear Orbi RBE361 (10.168.168.1), FW=V12.1.13_5.1.12, WiFi=WPA2, Devices~7, DNS=Router DNS filtering.