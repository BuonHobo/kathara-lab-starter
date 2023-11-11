# lab.conf
`nomemacchina[ethX]=nomelan`

# nomemacchina.startup
## IP address
IP address: `ip a add indirizzoproprio/netmask dev ethX`
## Static routing
Default route: `ip route add default via indirizzoprossimorouter dev ethX`

Static route: `ip route add lan/netmask via indirizzoprossimorouter dev ethX`

## Start Services
FRR: `systemctl start frr`

Apache2: `systemctl start apache2`

DNS: `systemctl start named`

# RIP
Va tutto sotto `router rip`

Specificare LAN su cui parlare RIP: `network lan/netmask`

Annunciare rotta: `route lan/netmask`

Ridistribuisci le connesse: `redistribute connected`

Ridistribuisci rotte ospf: `redistribute ospf`

# OSPF
Se ci sono costi va specificato usando:
```
interface ethX
ospf cost YY
```

Il resto va tutto sotto `router ospf`

Specificare LAN su cui parlare OSPF: `network lan/netmask area X.Y.W.Z`

Se una LAN è stub va scritto: `area X.Y.W.Z stub`

Annunciare rotta: `route lan/netmask`

Ridistribuisci le connesse: `redistribute connected`

Ridistribuisci rotte RIP: `redistribute rip`

# APACHE2

L'index si trova in `/var/www/html/index.html`

# vtysh

Vedere le rotte nel control plane: `show ip route`

`show ip ospf route`

`show ip ospf interface`

`show ip ospf neighbor`

`show ip ospf database`