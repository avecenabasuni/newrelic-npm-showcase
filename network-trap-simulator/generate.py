import os
import time
import random
import logging
import socket
import asyncio
from datetime import datetime
from pysnmp.hlapi.v1arch.asyncio import *

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Configuration from env vars
TRAP_TARGET = os.getenv('TRAP_TARGET', 'ktraps')
TRAP_PORT = int(os.getenv('TRAP_PORT', 1620))
INTERVAL_SEC = int(os.getenv('INTERVAL_SEC', 15))
INCIDENT_PROBABILITY = float(os.getenv('INCIDENT_PROBABILITY', 0.15))

# Global state
START_TIME = time.time()
snmp_dispatcher = SnmpDispatcher()

# Device Registry
DEVICES = {
    'cisco-router': {'hostname': 'id-jkt-rtr-01', 'ip': '10.10.0.10'},
    'cisco-switch': {'hostname': 'id-jkt-dsw-01', 'ip': '10.10.0.11'},
    'linksys-router': {'hostname': 'id-jkt-fw-01', 'ip': '10.10.0.12'},
    'linux-server': {'hostname': 'id-jkt-srv-01', 'ip': '10.10.0.13'},
    'mikrotik-router': {'hostname': 'id-jkt-mkt-01', 'ip': '10.10.0.14'},
}

def get_uptime_ticks():
    """Returns uptime in hundredths of a second (TimeTicks)."""
    return int((time.time() - START_TIME) * 100)

async def wait_for_target():
    """Retry connection to TRAP_TARGET with exponential backoff on startup."""
    backoff = 2
    max_retries = 5
    retries = 0
    
    while retries < max_retries:
        try:
            # We just need to resolve the address to confirm the target is up
            socket.gethostbyname(TRAP_TARGET)
            logging.info(f"[READY] Connected to {TRAP_TARGET}:{TRAP_PORT}")
            return
        except socket.gaierror:
            logging.info(f"Target {TRAP_TARGET} not reachable yet. Retrying in {backoff} seconds...")
            await asyncio.sleep(backoff)
            backoff *= 2
            retries += 1
            
    logging.warning(f"Could not resolve {TRAP_TARGET} after {max_retries} attempts. Proceeding anyway.")

async def send_trap(device_key, trap_oid, varbinds=None):
    """
    Sends an SNMPv2c trap to the configured destination using pysnmp hlapi v1arch asyncio.
    Injects agentAddress into the PDU payload.
    """
    dev = DEVICES[device_key]
    
    if varbinds is None:
        varbinds = []
        
    # Standard mandatory varbinds for SNMPv2 Trap + Our agent address specification
    base_varbinds = [
        ObjectType(ObjectIdentity('1.3.6.1.2.1.1.3.0'), TimeTicks(get_uptime_ticks())),
        ObjectType(ObjectIdentity('1.3.6.1.6.3.1.1.4.1.0'), ObjectIdentifier(trap_oid)),
        ObjectType(ObjectIdentity('1.3.6.1.6.3.18.1.3.0'), IpAddress(dev['ip'])) # agentAddress
    ]
    
    for oid, val in varbinds:
        base_varbinds.append(ObjectType(ObjectIdentity(oid), val))
        
    notification = NotificationType(ObjectIdentity(trap_oid))
    # Note: NotificationType automatically prepends sysUpTime and snmpTrapOID.
    # However we're providing them explicitly to ensure compliance and inject agentAddress correctly.
    # pysnmp allows manually supplying them.
    # ACTUALLY, NotificationType replaces them if we use plain ObjectType items.
    notification.add_varbinds(*base_varbinds)
    
    target = await UdpTransportTarget.create((TRAP_TARGET, TRAP_PORT))
    
    errorIndication, errorStatus, errorIndex, varBinds = await send_notification(
        snmp_dispatcher,
        CommunityData('public', mpModel=1), # mpModel=1 is SNMPv2c
        target,
        'trap',
        notification
    )
    
    if errorIndication:
        logging.error(f"Failed to send trap: {errorIndication}")
    # Else success (no output needed as we want just the incident markers)

def random_ip():
    return f"{random.randint(10, 192)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

def random_mac():
    return f"{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}.{random.randint(1000,9999)}.{random.randint(1000,9999)}"

async def generate_normal_mode():
    device = random.choice(list(DEVICES.keys()))
    
    if device == 'cisco-router':
        traps = [
            ('1.3.6.1.6.3.1.1.5.4', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(f"GigabitEthernet0/{random.randint(1, 4)}"))]), # linkUp
            ('1.3.6.1.6.3.1.1.5.3', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(f"GigabitEthernet0/{random.randint(1, 4)}"))]), # linkDown
            ('1.3.6.1.4.1.9.10.138.0.2', [('1.3.6.1.4.1.9.10.138.1.1.1.2.1', IpAddress(random_ip()))]), # ospfNbrStateChange
            ('1.3.6.1.4.1.9.9.187.0.0.1', [('1.3.6.1.4.1.9.9.187.1.2.5.1.28.1', OctetString(random_ip()))]), # bgpPeer Flap
            ('1.3.6.1.4.1.9.9.109.1.2.4.1.2', [('1.3.6.1.4.1.9.9.109.1.2.4.1.4', Integer32(random.randint(80, 95)))]), # CPU threshold
        ]
    elif device == 'cisco-switch':
        traps = [
            ('1.3.6.1.2.1.17.0.1', []), # spanning tree topology change
            ('1.3.6.1.4.1.9.9.315.0.0.1', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(f"Gi1/0/{random.randint(1, 48)}"))]), # port security
            ('1.3.6.1.4.1.9.9.41.2.0.1', [('1.3.6.1.4.1.9.9.41.1.2.3.1.5', OctetString("MACFLAP"))]), # MAC flap
            ('1.3.6.1.4.1.9.9.68.1.2.2.1.2', [('1.3.6.1.4.1.9.9.68.1.2.2.1.1', Integer32(random.randint(10, 100)))]), # VLAN change
            ('1.3.6.1.4.1.9.9.402.0.1', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(f"Gi1/0/{random.randint(1, 48)}"))]), # PoE denied
        ]
    elif device == 'linksys-router':
        traps = [
            ('1.3.6.1.6.3.1.1.5.4', [('1.3.6.1.2.1.2.2.1.2.1', OctetString("WAN"))]), # linkUp
            ('1.3.6.1.6.3.1.1.5.3', [('1.3.6.1.2.1.2.2.1.2.1', OctetString("WAN"))]), # linkDown
            ('1.3.6.1.4.1.4000.1.1.1', [('1.3.6.1.4.1.4000.1.1.2', Integer32(random.randint(80, 99)))]), # DHCP near capacity
            ('1.3.6.1.4.1.4000.2.1.1', [('1.3.6.1.4.1.4000.2.1.2', Integer32(random.randint(1000, 4000)))]), # NAT threshold
        ]
    elif device == 'linux-server':
        traps = [
            ('1.3.6.1.4.1.2021.251.1', [('1.3.6.1.4.1.2021.9.1.2.1', OctetString("/var")), ('1.3.6.1.4.1.2021.9.1.9.1', Integer32(random.randint(80, 95)))]), # UCD disk
            ('1.3.6.1.4.1.2021.254.1', []), # UCD memory
            ('1.3.6.1.4.1.2021.250.1', []), # UCD load
            ('1.3.6.1.6.3.1.1.5.3', [('1.3.6.1.2.1.2.2.1.2.1', OctetString("eth0"))]), # linkDown
        ]
    elif device == 'mikrotik-router':
        traps = [
            ('1.3.6.1.6.3.1.1.5.4', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(f"ether{random.randint(1, 5)}"))]), # linkUp
            ('1.3.6.1.6.3.1.1.5.3', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(f"ether{random.randint(1, 5)}"))]), # linkDown
            ('1.3.6.1.4.1.14988.1.1.6.1', [('1.3.6.1.4.1.14988.1.1.6.1.1', OctetString(random_ip()))]), # Login fail
            ('1.3.6.1.4.1.14988.1.1.1.1', [('1.3.6.1.4.1.14988.1.1.1.1.2', Integer32(random.randint(100, 500)))]), # firewall 
        ]
    
    choice = random.choice(traps)
    await send_trap(device, choice[0], choice[1])

async def incident_bgp_failover():
    logging.info(f"[INCIDENT] BGP failover triggered at {datetime.now().isoformat()}")
    peer_ip = random_ip()
    # 1. linkDown
    await send_trap('cisco-router', '1.3.6.1.6.3.1.1.5.3', [('1.3.6.1.2.1.2.2.1.2.1', OctetString("GigabitEthernet0/0"))])
    await asyncio.sleep(0.5)
    # 2. peer down
    await send_trap('cisco-router', '1.3.6.1.4.1.9.9.187.0.0.1', [
        ('1.3.6.1.4.1.9.9.187.1.2.5.1.28.1', OctetString(peer_ip)), 
        ('1.3.6.1.4.1.9.9.187.1.2.5.1.29.1', Integer32(3)) # Down
    ])
    await asyncio.sleep(1.0)
    # 3. spanning tree topology change
    await send_trap('cisco-switch', '1.3.6.1.2.1.17.0.1', [])
    await asyncio.sleep(3.0)
    # 4. linkUp
    await send_trap('cisco-router', '1.3.6.1.6.3.1.1.5.4', [('1.3.6.1.2.1.2.2.1.2.1', OctetString("GigabitEthernet0/0"))])
    # 5. peer restored
    await send_trap('cisco-router', '1.3.6.1.4.1.9.9.187.0.0.2', [
        ('1.3.6.1.4.1.9.9.187.1.2.5.1.28.1', OctetString(peer_ip)), 
        ('1.3.6.1.4.1.9.9.187.1.2.5.1.29.1', Integer32(1)) # Up
    ])

async def incident_port_security():
    logging.info(f"[INCIDENT] Port security violation triggered at {datetime.now().isoformat()}")
    port = f"Gi1/0/{random.randint(10, 48)}"
    mac = random_mac()
    
    # 1. port security violation
    await send_trap('cisco-switch', '1.3.6.1.4.1.9.9.315.0.0.1', [
        ('1.3.6.1.2.1.2.2.1.2.1', OctetString(port)),
        ('1.3.6.1.4.1.9.9.315.1.2.1.1.10', OctetString(mac))
    ])
    await asyncio.sleep(0.2)
    # 2. linkDown
    await send_trap('cisco-switch', '1.3.6.1.6.3.1.1.5.3', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(port))])
    await asyncio.sleep(0.5)
    # 3. firewall traffic spike
    await send_trap('linksys-router', '1.3.6.1.4.1.4000.2.1.1', [('1.3.6.1.4.1.4000.2.1.2', Integer32(12000))])
    await asyncio.sleep(5.0)
    # 4. linkUp
    await send_trap('cisco-switch', '1.3.6.1.6.3.1.1.5.4', [('1.3.6.1.2.1.2.2.1.2.1', OctetString(port))])

async def incident_server_exhaustion():
    logging.info(f"[INCIDENT] Server resource exhaustion triggered at {datetime.now().isoformat()}")
    
    # 1. UCD disk full
    await send_trap('linux-server', '1.3.6.1.4.1.2021.251.1', [
        ('1.3.6.1.4.1.2021.9.1.2.1', OctetString("/var")), 
        ('1.3.6.1.4.1.2021.9.1.9.1', Integer32(random.randint(98, 100)))
    ])
    await asyncio.sleep(1.0)
    # 2. UCD memory exceeded
    await send_trap('linux-server', '1.3.6.1.4.1.2021.254.1', [])
    await asyncio.sleep(2.0)
    # 3. Router ospf down
    await send_trap('cisco-router', '1.3.6.1.4.1.9.10.138.0.2', [
        ('1.3.6.1.4.1.9.10.138.1.1.1.2.1', IpAddress('10.10.0.13'))
    ])
    await asyncio.sleep(5.0)
    # 4. Recovery
    await send_trap('linux-server', '1.3.6.1.4.1.2021.251.2', [ # simulated disk okay
        ('1.3.6.1.4.1.2021.9.1.2.1', OctetString("/var")), 
        ('1.3.6.1.4.1.2021.9.1.9.1', Integer32(70))
    ])
    await send_trap('cisco-router', '1.3.6.1.4.1.9.10.138.0.2', [ # simulating OSPF adjacency up, using same base OID for simplicity here
        ('1.3.6.1.4.1.9.10.138.1.1.1.2.1', IpAddress('10.10.0.13'))
    ])

async def main():
    logging.info("Starting Network Trap Simulator...")
    await wait_for_target()
    logging.info(f"Interval: {INTERVAL_SEC}s, Incident Prob: {INCIDENT_PROBABILITY}")
    
    incidents = [
        incident_bgp_failover,
        incident_port_security,
        incident_server_exhaustion
    ]

    while True:
        if random.random() < INCIDENT_PROBABILITY:
            incident = random.choice(incidents)
            await incident()
        else:
            await generate_normal_mode()
            
        await asyncio.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nExiting simulator.")
