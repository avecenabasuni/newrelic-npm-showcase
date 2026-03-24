# LinkedIn Post

I spent the weekend building a network monitoring lab with zero physical devices.

No routers. No switches. No cables. Just Docker.

The thing that bugged me: New Relic's NPM documentation is scattered. SNMP polling lives in one guide, traps in another, syslog somewhere else, NetFlow in a fourth. Nobody stitched them together. So I wrote the tutorial I wished existed.

Five simulated network devices (Cisco router, Cisco switch, Linksys router, Linux server, MikroTik router) running via snmpsim. All telemetry shipped through ktranslate. SNMP polling, SNMP traps, syslog, and NetFlow, all feeding into a single New Relic account.

The whole stack runs in Docker. You can have it working in under an hour.

I also built custom trap and syslog simulators that generate realistic incident scenarios. A BGP session drops because the upstream server crashes. Interfaces go down across multiple devices at once. The kind of correlated events you'd see in production, not random noise.

This wouldn't exist without Andi, who mentored me when he was at New Relic and I was at Berca. His original guide gave me the foundation. I extended it with traps, syslog, incident simulation, and a full containerized lab.

Full article and repo:
[LINK]

\#NewRelic #NetworkMonitoring #SNMP #Docker #Observability #NPM #NetworkEngineering #DevOps #ktranslate
