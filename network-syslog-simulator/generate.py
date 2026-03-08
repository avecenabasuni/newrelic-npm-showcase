import os
import socket
import time
import random
import logging
from datetime import datetime

# Setup logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Configuration
SYSLOG_TARGET = os.getenv('SYSLOG_TARGET', 'ksyslog')
SYSLOG_PORT = int(os.getenv('SYSLOG_PORT', 5143))
INTERVAL_SEC = int(os.getenv('INTERVAL_SEC', 10))
INCIDENT_PROBABILITY = float(os.getenv('INCIDENT_PROBABILITY', 0.15))

# Setup socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Facilities
FAC_DAEMON = 3
FAC_AUTH = 4
FAC_LOCAL6 = 22
FAC_LOCAL7 = 23

# Severities
SEV_EMERG = 0
SEV_ALERT = 1
SEV_CRIT = 2
SEV_ERR = 3
SEV_WARNING = 4
SEV_NOTICE = 5
SEV_INFO = 6
SEV_DEBUG = 7

# Device Registry
DEVICES = {
    'cisco-router': {'hostname': 'id-jkt-rtr-01', 'ip': '10.10.0.10', 'fac': FAC_LOCAL7},
    'cisco-switch': {'hostname': 'id-jkt-dsw-01', 'ip': '10.10.0.11', 'fac': FAC_LOCAL7},
    'linksys-router': {'hostname': 'id-jkt-fw-01', 'ip': '10.10.0.12', 'fac': FAC_LOCAL6},
    'linux-server': {'hostname': 'id-jkt-srv-01', 'ip': '10.10.0.13', 'fac': FAC_DAEMON},
    'mikrotik-router': {'hostname': 'id-jkt-mkt-01', 'ip': '10.10.0.14', 'fac': FAC_LOCAL6},
}

def get_current_time():
    # RFC 3164 format: MMM DD HH:MM:SS
    # Single digit day must have leading space, padded
    t = datetime.now()
    return t.strftime("%b %e %H:%M:%S")

def send_syslog(device_key, severity, program, message, override_fac=None):
    dev = DEVICES[device_key]
    fac = override_fac if override_fac is not None else dev['fac']
    pri = (fac * 8) + severity
    timestamp = get_current_time()
    
    syslog_msg = f"<{pri}>{timestamp} {dev['hostname']} {program}: {message}"
    b_msg = syslog_msg.encode('utf-8')
    
    try:
        sock.sendto(b_msg, (SYSLOG_TARGET, SYSLOG_PORT))
    except Exception as e:
        err_msg = f"Error sending syslog to {SYSLOG_TARGET}:{SYSLOG_PORT} - {str(e)}"
        if "Bad fd" not in err_msg and "gaierror" not in err_msg:
            # We don't want to flood logs with DNS failures if it's transient
            logging.error(err_msg)

def random_ip():
    return f"{random.randint(10, 192)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

def generate_normal_mode():
    device = random.choice(list(DEVICES.keys()))
    
    if device == 'cisco-router':
        msgs = [
            (SEV_INFO, 'BGP', f"%BGP-5-ADJCHANGE: neighbor {random_ip()} Up"),
            (SEV_NOTICE, 'OSPF', f"%OSPF-5-ADJCHG: Process 1, Nbr {random_ip()} on GigabitEthernet0/0 from FULL to DOWN, Neighbor Down: Dead timer expired"),
            (SEV_INFO, 'LINK', f"%LINK-3-UPDOWN: Interface GigabitEthernet0/{random.randint(1, 4)}, changed state to up"),
            (SEV_WARNING, 'SYS', f"%SYS-4-CPUHOG: Task run time exceeded (80%), Process = IP Input"),
            (SEV_INFO, 'MPLS', f"%LDP-5-NBRCHG: LDP Neighbor {random_ip()}:0 is UP")
        ]
    elif device == 'cisco-switch':
        msgs = [
            (SEV_NOTICE, 'SPANTREE', f"%SPANTREE-5-TOPOTRAP: Topology Change Trap for vlan {random.randint(10, 100)}"),
            (SEV_WARNING, 'PM', f"%PM-4-ERR_DISABLE: psecure-violation error detected on Gi1/0/{random.randint(1,48)}, putting Gi1/0/{random.randint(1,48)} in err-disable state"),
            (SEV_NOTICE, 'SW_MATM', f"%SW_MATM-4-MACFLAP_NOT: Host {random.choice(['001A.2B3C','002B.3C4D','003C.4D5E'])}.4D5{random.randint(1,9)} in vlan {random.randint(1, 50)} is flapping between port Gi1/0/{random.randint(1,24)} and port Gi1/0/{random.randint(25,48)}"),
            (SEV_INFO, 'VTP', f"%VTP-5-VLANCHG: VLAN {random.randint(100, 200)} has been created by {random_ip()}"),
            (SEV_WARNING, 'ILPOWER', f"%ILPOWER-4-PWR_DENIED: Interface Gi1/0/{random.randint(1,48)}: inline power denied")
        ]
    elif device == 'linksys-router':
        msgs = [
            (SEV_INFO, 'dhcpd', f"DHCPACK on 192.168.1.{random.randint(100,200)} to 00:{random.randint(10,99)}:ab:cd:ef:12 via eth1"),
            (SEV_NOTICE, 'dhcpd', f"DHCPEXPIRE on 192.168.1.{random.randint(100,200)} for 00:{random.randint(10,99)}:ab:cd:ef:12"),
            (SEV_WARNING, 'kernel', f"nf_conntrack: table full, dropping packet"),
            (SEV_INFO, 'pppd', f"WAN interface ppp0 reconnected"),
            (SEV_NOTICE, 'dnsmasq', f"query[A] random-domain-{random.randint(10,99)}.com from 192.168.1.{random.randint(10,50)} forwarded directly"),
            (SEV_WARNING, 'watchdog', f"firmware watchdog triggered, system stable")
        ]
    elif device == 'linux-server':
        msgs = [
            (SEV_WARNING, 'sshd', f"Failed password for invalid user admin from {random_ip()} port {random.randint(30000, 60000)} ssh2", FAC_AUTH),
            (SEV_NOTICE, 'sshd', f"Accepted publickey for root from {random_ip()} port {random.randint(30000, 60000)} ssh2", FAC_AUTH),
            (SEV_WARNING, 'kernel', f"disk usage warning on /var: 8{random.randint(0,9)}% used"),
            (SEV_ERR, 'kernel', f"Out of memory: Killed process {random.randint(1000, 9000)} (python3) total-vm as {random.randint(20000, 50000)}kB"),
            (SEV_INFO, 'systemd', f"Started Nginx Web Server."),
            (SEV_WARNING, 'CRON', f"cron job /usr/local/bin/backup.sh failed with exit code 1")
        ]
    elif device == 'mikrotik-router':
        msgs = [
            (SEV_WARNING, 'firewall', f"forward: in:ether1 out:bridge1, src-mac 12:34:56:78:90:ab, proto TCP (SYN), {random_ip()}:{random.randint(1024,65535)}->10.10.0.50:445, len 52, drop"),
            (SEV_INFO, 'dhcp', f"defconf assigned 10.10.0.{random.randint(100,200)} to 00:11:22:33:44:55"),
            (SEV_NOTICE, 'interface', f"ether2 link up (1000MBit/s)"),
            (SEV_WARNING, 'system', f"login failure for user admin from {random_ip()} via ssh"),
            (SEV_NOTICE, 'bgp', f"peer {random_ip()} established")
        ]
    
    msg = random.choice(msgs)
    if len(msg) == 4:
        send_syslog(device, msg[0], msg[1], msg[2], msg[3])
    else:
        send_syslog(device, msg[0], msg[1], msg[2])

def trigger_incident_bgp_failover():
    logging.info(f"[INCIDENT] BGP failover triggered at {datetime.now().isoformat()}")
    downstream_ip = random_ip()
    
    send_syslog('cisco-router', SEV_ERR, 'BGP', f"%BGP-3-NOTIFICATION: sent to neighbor {downstream_ip} 4/0 (hold timer expired) 0 bytes")
    time.sleep(random.uniform(0.1, 0.5))
    send_syslog('cisco-switch', SEV_NOTICE, 'SPANTREE', f"%SPANTREE-5-TOPOTRAP: Topology Change Trap for vlan 1")
    time.sleep(random.uniform(0.1, 0.5))
    send_syslog('linux-server', SEV_ERR, 'app-service', f"Connection timeout to downstream payment-gateway at {downstream_ip}:443")
    time.sleep(random.uniform(0.1, 0.5))
    send_syslog('cisco-router', SEV_NOTICE, 'BGP', f"%BGP-5-ADJCHANGE: neighbor {downstream_ip} Down BGP Notification sent")
    time.sleep(random.uniform(0.5, 1.5))
    send_syslog('cisco-router', SEV_INFO, 'BGP', f"%BGP-5-ADJCHANGE: neighbor {downstream_ip} Up")

def trigger_incident_port_security():
    logging.info(f"[INCIDENT] Port security violation triggered at {datetime.now().isoformat()}")
    mac1 = "000C.29AB." + str(random.randint(1000, 9999))
    mac2 = "000C.29AB." + str(random.randint(1000, 9999))
    port = f"Gi1/0/{random.randint(10, 20)}"
    
    send_syslog('cisco-switch', SEV_WARNING, 'SW_MATM', f"%SW_MATM-4-MACFLAP_NOT: Host {mac1} in vlan 10 is flapping between port {port} and port {port}")
    time.sleep(random.uniform(0.1, 0.5))
    send_syslog('cisco-switch', SEV_ERR, 'PM', f"%PM-4-ERR_DISABLE: psecure-violation error detected on {port}, putting {port} in err-disable state")
    time.sleep(random.uniform(0.1, 0.5))
    send_syslog('linksys-router', SEV_WARNING, 'kernel', f"nf_conntrack: unusual traffic spike detected from Segment 10")
    time.sleep(random.uniform(1.0, 2.0))
    send_syslog('cisco-switch', SEV_NOTICE, 'PM', f"%PM-4-ERR_RECOVER: Attempting to recover from psecure-violation err-disable state on {port}")
    send_syslog('cisco-switch', SEV_INFO, 'LINK', f"%LINK-3-UPDOWN: Interface {port}, changed state to up")

def trigger_incident_server_exhaustion():
    logging.info(f"[INCIDENT] Server resource exhaustion triggered at {datetime.now().isoformat()}")
    
    send_syslog('linux-server', SEV_WARNING, 'kernel', f"disk usage warning on /var: 98% used")
    time.sleep(random.uniform(0.1, 0.3))
    send_syslog('linux-server', SEV_CRIT, 'kernel', f"Out of memory: Killed process {random.randint(2000, 3000)} (postgres) total-vm as 5242880kB")
    time.sleep(random.uniform(0.1, 0.3))
    send_syslog('linux-server', SEV_ERR, 'systemd', f"postgresql.service: Main process exited, code=killed, status=9/KILL")
    time.sleep(random.uniform(0.5, 1.0))
    send_syslog('linux-server', SEV_NOTICE, 'systemd', f"postgresql.service: Succeeded and service restored")
    send_syslog('cisco-router', SEV_WARNING, 'OSPF', f"%OSPF-5-ADJCHG: Process 1, Nbr 10.10.0.13 on GigabitEthernet0/1 from FULL to DOWN, Neighbor Down: Dead timer expired")
    time.sleep(random.uniform(0.3, 0.8))
    send_syslog('cisco-router', SEV_INFO, 'OSPF', f"%OSPF-5-ADJCHG: Process 1, Nbr 10.10.0.13 on GigabitEthernet0/1 from LOADING to FULL, Loading Done")


if __name__ == "__main__":
    logging.info(f"Starting Network Syslog Simulator...")
    logging.info(f"Target: {SYSLOG_TARGET}:{SYSLOG_PORT}")
    logging.info(f"Interval: {INTERVAL_SEC}s, Incident Prob: {INCIDENT_PROBABILITY}")
    
    incidents = [
        trigger_incident_bgp_failover,
        trigger_incident_port_security,
        trigger_incident_server_exhaustion
    ]

    while True:
        # Check if we should trigger an incident
        if random.random() < INCIDENT_PROBABILITY:
            incident = random.choice(incidents)
            incident()
        else:
            # Generate 1 to 2 random normal messages
            for _ in range(random.randint(1, 2)):
                generate_normal_mode()
                
        time.sleep(INTERVAL_SEC)
