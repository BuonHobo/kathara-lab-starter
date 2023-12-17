from __future__ import annotations
from pathlib import Path
from daemon.classes import Daemon, DaemonConfigurer
from topology.classes import Router


class DNSConfigurer(DaemonConfigurer):
    def __init__(self, dns: DNSDaemon) -> None:
        self.dns = dns

    def configure(self, router: Router, path: Path, data: Path):
        #
        # Configures resolver for clients and then returns
        #
        path.joinpath("etc").mkdir(exist_ok=True)
        if router in self.dns.clients_to_resolver:
            with path.joinpath("etc/resolv.conf").open("w") as f:
                f.write(
                    f"nameserver {self.dns.clients_to_resolver[router].router_id}\n"
                )
            return

        #
        # Starts named for name servers and resolvers
        #
        with path.parent.joinpath(f"{router.name}.startup").open("a") as f:
            f.write("\nsystemctl start named\n")

        path = path.joinpath("etc/bind")
        path.mkdir()

        #
        # Configures named.conf.options for name servers and resolvers
        #
        with path.joinpath("named.conf.options").open("w") as f:
            f.write('options {\n    directory "/var/cache/bind";\n')
            if router in self.dns.resolvers:
                f.write("    allow-recursion { 0/0;};\n    dnssec-validation no;\n")
            f.write("};")

        #
        # Configures named.conf for name servers and resolvers
        #
        with path.joinpath("named.conf").open("w") as f:
            f.write('include "/etc/bind/named.conf.options";\n\n')

            f.write('zone "." {\n')
            f.write(
                f'    type {"master" if router==self.dns.rootserver else "hint"};\n'
            )
            f.write('    file "/etc/bind/db.root";\n};\n\n')

            for zone in self.dns.routers_to_zones[router]:
                if zone.parent is None:
                    continue
                name = zone.get_full_name().removesuffix(".")
                f.write(
                    f'zone "{name}" {"{"}\n    type master;\n    file "/etc/bind/db.{name}";\n{"}"};\n\n'
                )

        #
        # Configures dbs for zone authorities and hints for root
        #
        for zone in self.dns.routers_to_zones[router]:
            with path.joinpath(
                f"db.{'root' if zone.parent is None else zone.get_full_name().removesuffix('.')}"
            ).open("w") as f:
                out = f"""$TTL 60000
@    IN    SOA    {"ROOT-SERVER" if zone.parent is None else zone.server.name}.{zone.get_full_name()}    root.{"ROOT-SERVER" if zone.parent is None else zone.server.name}.{zone.get_full_name()} ( 
    2006031201 ; serial
    28 ; refresh
    14 ; retry
    3600000 ; expire
    0 ; negative cache ttl
    )
    
@               IN      NS      {"ROOT-SERVER" if zone.parent is None else zone.server.name}.{zone.get_full_name()}
{"ROOT-SERVER" if zone.parent is None else zone.server.name}.{zone.get_full_name()}    IN      A       {router.router_id}

"""
                for child in zone.children:
                    out += f"{child.get_full_name()}            IN      NS      {child.server.name}.{child.get_full_name()}\n"
                    out += f"{child.server.name}.{child.get_full_name()}        IN      A       {child.server.router_id}\n\n"

                for router in zone.names:
                    out += f"{router.name}.{zone.get_full_name()}       IN      A      {router.router_id}\n"

                f.write(out)
        if router != self.dns.rootserver:
            with path.joinpath("db.root").open("w") as f:
                f.write(
                    f".                   IN  NS    ROOT-SERVER.\nROOT-SERVER.        IN  A     {self.dns.rootserver.router_id}"
                )


class DNSDaemon(Daemon):
    def __init__(self, root: Zone) -> None:
        self.routers_to_zones: dict[Router, list[Zone]] = {}
        self.resolvers: set[Router] = set()
        self.clients_to_resolver: dict[Router, Router] = {}
        self.add_root_tree(root)

    def add_router(self, router: Router) -> None:
        self.routers_to_zones[router] = []
        return super().add_router(router)

    def add_resolver(self, router: Router) -> None:
        self.resolvers.add(router)
        self.add_router(router)

    def add_client(self, client: Router, resolver: Router) -> None:
        self.clients_to_resolver[client] = resolver
        self.add_router(client)

    def add_root_tree(self, root: Zone):
        self.rootserver = root.server
        self.add_zone_tree(root)

    def add_zone_tree(self, zone: Zone):
        self.add_router(zone.server)
        self.routers_to_zones[zone.server].append(zone)
        for child in zone.children:
            self.add_zone_tree(child)

    def get_configurer(self) -> DaemonConfigurer:
        return DNSConfigurer(self)


class Zone:
    def __init__(
        self,
        name: str,
        parent: Zone | None,
        server: Router,
        names:list[Router]
    ) -> None:
        self.name = name
        self.names: set[Router] = set(names)
        self.parent = parent
        self.server = server
        self.children: list[Zone] = []

    def add_child(self, zone: Zone):
        self.children.append(zone)

    def add_name(self, router: Router):
        self.names.add(router)

    def get_full_name(self) -> str:
        if self.parent is not None:
            return self.name + "." + self.parent.get_full_name()
        else:
            return self.name
