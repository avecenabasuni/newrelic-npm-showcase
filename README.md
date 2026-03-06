# New Relic SNMP Monitoring: Multi-Vendor Performance Showcase

Transform your network into a transparent observability ecosystem using Docker and simulated telemetry.

## The Problem: Network Black Boxes

Monitoring modern network infrastructure often requires expensive hardware or complex lab setups just to test basic metric ingestion. Without visibility, critical events like BGP session drops or interface errors remain hidden until they impact users.

## The Solution: One-Click Telemetry Simulation

This repository provides a production-grade SNMP record library and simulation framework. By leveraging Docker and Kentik ktranslate, you can stream real-world telemetry from varied vendors directly into New Relic in minutes.

### Key Value Propositions
* **Zero Cost Testing:** Simulate high-end Cisco and MikroTik hardware without the hardware.
* **Unified Observability:** Bridge the gap between server logs and network metrics.
* **Rapid Deployment:** Go from empty dashboard to full visibility in one afternoon.

## Getting Started

Follow these steps to initialize your monitoring stack.

### 1. Configure New Relic
Ensure you have your License Key and Account ID ready.

```bash
export NR_ACCOUNT_ID="your_account_id"
export NR_LICENSE_KEY="your_license_key"
```

### 2. Deploy the Network Simulator
Create a bridge network and launch the device containers.

```bash
docker network create --subnet 10.10.0.0/24 testnet

# Example: Run the Cisco Router
docker run -d --name cisco-router --network testnet --ip 10.10.0.10 \
  -v $(pwd)/snmp-record/cisco-router:/usr/local/snmpsim/data \
  tandrup/snmpsim
```

### 3. Translate and Ingest
Use ktranslate to poll the simulated devices and ship metrics to New Relic.

## Device Library

This repository includes pre-configured SNMP records for:
* **Cisco Router:** IOS-standard system and interface metrics.
* **Cisco Switch:** Layer 2/3 switching telemetry.
* **Linksys Router:** Consumer-grade gateway simulation.
* **Linux Server:** Application server health (UCD-SNMP).
* **MikroTik Router:** Advanced multi-vendor showcase with RB750Gr3 records.

## ROI and Impact

By implementing this stack, engineering teams achieve:
* **Lower MTTR:** Identify the root cause of network issues instantly through correlation.
* **Better Capacity Planning:** Use high-fidelity flow data to predict bandwidth needs.
* **Reduced Risk:** Test monitoring alerts and automation in a safe, simulated sandbox.

---

Built with precision for the New Relic community.
