# lab.conf
`nomemacchina[ethX]=nomelan`

# nomemacchina.startup
## IP address
IP address: `ip a add <indirizzoproprio>/<netmask> dev ethX`
## Static routing
Default route: `ip route add default via <indirizzonexthop> dev ethX`

Static route: `ip route add <prefisso>/<netmask> via <indirizzonexthop> dev ethX`

## Start Services
FRR: `systemctl start frr`

Apache2: `systemctl start apache2`

[DNS](https://github.com/KatharaFramework/Kathara-Labs/blob/main/main-labs/application-level/dns/010-kathara-lab_dns.pdf): `systemctl start named`

# RIP
Va tutto sotto `router rip`

Specificare LAN su cui parlare RIP: `network <prefisso>/<netmask>`

Annunciare rotta: `route <lan>/<netmask>`

Ridistribuisci le connesse: `redistribute connected`

Ridistribuisci le statiche: `redistribute static`

Ridistribuisci rotte ospf: `redistribute ospf`

# OSPF
Se ci sono costi va specificato usando:
```
interface ethX
ospf cost YY
```

Il resto va tutto sotto `router ospf`

Specificare LAN su cui parlare OSPF: `network <lan>/<netmask> area X.Y.W.Z`

Se una LAN è stub va scritto: `area X.Y.W.Z stub`

Annunciare rotta: `route <lan>/<netmask>`

Ridistribuisci le connesse: `redistribute connected`

Ridistribuisci le statiche: `redistribute static`

Ridistribuisci rotte RIP: `redistribute rip`

# APACHE2
L'index si trova in `/var/www/html/index.html`

# vtysh
Mostra la configurazione in uso: `show running config`

Mostra rotte nel control plane: `show ip route`

`show ip ospf route`

`show ip ospf interface`

`show ip ospf neighbor`

`show ip ospf database`

`show ip bgp`

`show ip bgp neighbors`

`show ip bgp summary`

# FRR
Aggiungere rotta statica: `ip route <prefisso>/<netmask> <indirizzonexthop>`

Aggiungere password zebra (da usare per connettersi a bgp tramite `telnet localhost bgpd`):
```
password zebra
enable password zebra
```
Definire una prefix-list: `ip prefix-list <p-list-name> [seq <seq_number>] {permit, deny} {<network/mask>, any}`

Specificare `seq <seq_number>` serve a dire l'ordine di precedenza delle regole, se è omesso allora conta l'ordine in cui sono scritte

Tutto ciò che non è esplicitamente `permit` viene considerato `deny`

# BGP
Le prefix list (viste) e le filter list (non viste) vanno fuori da BGP, fanno parte di FRR

Va tutto sotto `router bgp <my-as-number>`

## Peering
Crea peering con vicino: `neighbor <neighbor-ip> remote-as <neighbor-as-num>`

Aggiungi descrizione del vicino: `neighbor <neighbor-ip> description <text>`


## Announcement
Annuncia rotta: `network <network-ip/network-mask>`

Di base la annuncia solo se questa rotta esiste nel kernel, per disabilitarlo c'è `no bgp network import-check`

Di base la annuncia solo ai peer per cui c'è una policy che lo permette, per disabilitarlo c'è `no bgp ebgp-requires-policy`

Annunciare una rotta non la inietta nel kernel del router che la annuncia (ma nell'altro sì)

La rotta viene automaticamente "tagliata" in modo che corrisponda con la netmask

## Filtering
Utilizzare una prefix-list per un vicino: `neighbor <neighbor-ip> prefix-list <p-list-name> {in, out}`

`in` filtra gli annunci in ingresso (traffico in uscita), `out` filtra gli annunci in uscita (traffico in ingresso)

Se si usa una prefix-list non definita, allora verrà applicato un `deny` su tutto.

Specificare access-list usata come filter-list per vicino: `neighbor <neighbor-ip> filter-list <acl-name> {in, out}`

Definire una as-path access-list: `bgp as-path access-list <acl-name> {permit, deny} <regexp>`

## Tuning
Alcuni attributi da usare per il tuning sono:

`prefix`: La rotta annunciata. Obbligatorio

`as-path`: La lista AS attraversati da questa rotta. Obbligatorio

`origin`: Il protocollo di origine di questa rotta. Obbligatorio

`next-hop`: Il computer a cui inviare il traffico di questa rotta. Obbligatorio. I router i-bgp si comunicano il next-hop del router esterno che ha annunciato la rotta, quindi per conoscere il vero next-hop (quello all'interno dell'AS) viene usato un recursive lookup. In pratica si aspetta di ricevere la stessa rotta tramite un protocollo IGP e si usa il next-hop che sta lì.

`metric`: Costo della rotta. Si preferisce valore basso e viene usato tra AS diversi per comunicare preferenze sui collegamenti da utilizzare. Non è transitivo (non viene propagato dai vicini)

`local-pref`: Preferenza della rotta. Si preferisce un valore alto e viene usato all'interno dello stesso AS con i peer i-bgp per controllare il traffico

`community`: Un tag della rotta, ha un valore numerico che si può usare in molti modi. In genere per raggruppare rotte o usufruire di servizi dei customer.

### route-map
Il tuning degli attributi si fa attraverso le route-map.

Per specificare la route-map usata con un vicino: `neighbor <neighbor-ip> route-map <r-map-name> {in, out}`

Per definire una route-map:
```
route-map <r-map-name> {permit, deny} <seq-number>
match <announce-property>
set <attribute-setting>
...
```
Si possono avere più statement di questo tipo per la stessa route-map. Tra quelli adatti viene applicato quello con il sequence number più basso, o quello senza `match`. Se non ci sono statement adatti allora l'annuncio viene scartato.

Se si usa una route-map non definita allora viene in automatico viene negato ogni annuncio.

Il match si può fare sui vari parametri di bgp, qualche esempio è:

* `match as-path <WORD>` dove WORD è il nome della `bgp as-path access-list` che si sta usando
* `match ip address <acl-name>` per utilizzare una access list normale (senza as-path), cioè quella che di base matcha anche netmask più specifiche.
* `match ip address prefix-list <prefix-list-name>` dove ogni netmask è considerata separatamente

Una volta matchato l'annuncio, si può settare un parametro:

* `set metric <number>` la metric di default è 0???? Non sono sicuro
* `set local-preference <number` che di default è 100

### Scelta della best route
La best route viene scelta deterministicamente in base ad una gerarchia di attributi. Solamente la best route viene annunciata ai peer e solo se il next-hop è raggiungibile. Prefissi con netmask diverse sono considerati diversi.

1. largest weight
(cisco proprietary)
2. largest local preference
3. locally originated (by the router itself)
4. shortest as-path length
5. lowest origin (igp<egp<incomplete)
6. lowest multi-exit-discriminator
(Solo se entrambe le rotte provengono dallo stesso router)
7. prefer ebgp over ibgp (Così il traffico non deve attraversare il proprio AS)
8. lowest igp metric (to next-hop)
9. lowest router-id (of announcing peer)