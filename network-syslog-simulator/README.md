# Network Syslog Simulator

A lightweight Python-based tool that continuously generates realistic RFC 3164 syslog messages simulating a network environment with five devices (Routers, Switches, Linux Servers, and Firewalls).

It has two operating modes:

- **Normal Mode**: Generates random background noise (INFO/NOTICE messages) like DHCP leases fading, SSH logins passing, or OSPF hellos.
- **Incident Mode**: Controlled by a probability variable, this mode periodically triggers a burst of highly correlated multi-device log sequences (e.g., a server runs out of memory, crashes, and causes an OSPF route flap).

## How to Run

To run it alongside the tutorial's Docker network:

```bash
docker build -t network-syslog-simulator .

docker run -d \
  --name syslog-sim \
  --network testnet \
  -e SYSLOG_TARGET=ksyslog \
  -e SYSLOG_PORT=5143 \
  -e INTERVAL_SEC=10 \
  -e INCIDENT_PROBABILITY=0.15 \
  network-syslog-simulator
```

## Configuration

- `SYSLOG_TARGET`: Destination hostname/IP (default `ksyslog`)
- `SYSLOG_PORT`: Destination UDP port (default `5143`)
- `INTERVAL_SEC`: Seconds between log generation cycles (default `10`)
- `INCIDENT_PROBABILITY`: Chance per cycle to trigger an incident (default `0.15`)
