# Network Trap Simulator

A lightweight Python-based tool that continuously generates realistic SNMPv2c traps, simulating a network environment with five devices (Routers, Switches, Linux Servers, and Firewalls). 

It has two operating modes:

- **Normal Mode**: Generates random low-severity background noise such as `linkUp`, routine OSPF hello confirmations, and DHCP renewals.
- **Incident Mode**: Controlled by a probability variable, this mode periodically triggers a rapid, correlated burst of traps across multiple devices within a 2-3 second window, telling a specific network incident story.

## How to Run

To run it alongside the tutorial's Docker network:

```bash
docker build -t network-trap-simulator .

docker run -d \
  --name trap-sim \
  --network testnet \
  -e TRAP_TARGET=ktraps \
  -e TRAP_PORT=1620 \
  -e INTERVAL_SEC=15 \
  -e INCIDENT_PROBABILITY=0.15 \
  network-trap-simulator
```

## Configuration

- `TRAP_TARGET`: Destination hostname/IP (default `ktraps`)
- `TRAP_PORT`: Destination UDP port (default `1620`)
- `INTERVAL_SEC`: Seconds between log generation cycles (default `15`)
- `INCIDENT_PROBABILITY`: Chance per cycle to trigger an incident (default `0.15`)

## Trap Reference Table

| OID | Human-Readable Name | Device | Typical Severity |
| :--- | :--- | :--- | :--- |
| `1.3.6.1.6.3.1.1.5.3` | `linkDown` | Router/Switch/Server | Critical / Error |
| `1.3.6.1.6.3.1.1.5.4` | `linkUp` | Router/Switch/Server | Info / Notice |
| `1.3.6.1.4.1.9.9.187.0.0.1` | `cbgpPeer2FsmStateChange` (Down) | Cisco Router | Error |
| `1.3.6.1.4.1.9.9.187.0.0.2` | `cbgpPeer2FsmStateChange` (Up) | Cisco Router | Info |
| `1.3.6.1.2.1.17.0.1` | `newRoot` (Spanning Tree) | Cisco Switch | Notice |
| `1.3.6.1.4.1.9.9.315.0.0.1` | `cpsbPortSecurityViolation` | Cisco Switch | Warning / Error |
| `1.3.6.1.4.1.9.9.41.2.0.1` | `ccmMACFlap_Not` | Cisco Switch | Warning |
| `1.3.6.1.4.1.2021.251.1` | `dskTable` Full | Linux Server | Warning |
| `1.3.6.1.4.1.2021.254.1` | `prTable` OOM / Memory Exceeded | Linux Server | Critical |
| `1.3.6.1.4.1.9.10.138.0.2` | `ospfNbrStateChange` | Cisco Router | Info / Warning |

## Verification

> ⚠️ SNMP traps in New Relic do NOT appear in Logs. They are stored as a separate `KSnmpTrap` event type. The field names below (`src_addr`, `TrapOID`) are based on observed ktranslate behavior — verify them against your actual event schema by running `SELECT keyset() FROM KSnmpTrap LIMIT 1` first.

```sql
-- Discover actual field names in your environment first
SELECT keyset() FROM KSnmpTrap LIMIT 1

-- All traps in last 30 minutes
SELECT * FROM KSnmpTrap SINCE 30 MINUTES AGO LIMIT 20

-- Timeline from one device
SELECT * FROM KSnmpTrap 
WHERE src_addr = '10.10.0.10' 
SINCE 10 MINUTES AGO

-- Trap type breakdown
SELECT count(*) FROM KSnmpTrap 
FACET TrapOID 
SINCE 1 HOUR AGO
```

## Cross-Signal Correlation

Because `KSnmpTrap` and `Log` (syslog) are different data types in New Relic, they cannot be `JOIN`ed in a single basic NRQL query. To correlate trap and syslog data during an incident, open two separate NRQL tabs in New Relic with matching time windows:

```sql
-- Tab 1: Traps from router during incident
SELECT * FROM KSnmpTrap 
WHERE src_addr = '10.10.0.10' 
SINCE 10 MINUTES AGO

-- Tab 2: Syslog from same device during same window
SELECT * FROM Log 
WHERE hostname = 'id-jkt-rtr-01' 
SINCE 10 MINUTES AGO
```
