from __future__ import annotations
from pathlib import Path
from daemon.classes import Daemon, DaemonConfigurer
from topology.classes import Router


class DNSConfigurer(DaemonConfigurer):
    def __init__(self, dns: DNSDaemon) -> None:
        self.dns = dns

    def configure(self, router: Router, path: Path):
        path = path.joinpath("etc/bind")
        path.mkdir()

        with path.joinpath("named.conf.options").open("w") as f:
            f.write('options {\n    directory "/var/cache/bind";\n};')

        with path.joinpath("named.conf").open("w") as f:
            f.write('include "/etc/bind/named.conf.options";\n\n')

            f.write('zone "." {\n')
            f.write(
                f'    type {"master" if router==self.dns.rootserver else "hint"};\n'
            )
            f.write('    file "/etc/bind/db.root";\n};\n\n')

            for zone in self.dns.routers_to_zones[router]:
                if zone.name=="":
                    continue
                name = zone.get_full_name().removesuffix(".")
                f.write(
                    f'zone "{name}" {"{"}\n    type master;\n    file "/etc/bind/db.{name}";\n{"}"};\n\n'
                )

        for zone in self.dns.routers_to_zones[router]:
            pass

        if router!=self.dns.rootserver:
            with path.joinpath("db.root").open("w") as f:
                f.write(f'.                   IN  NS    ROOT-SERVER.\nROOT-SERVER.        IN  A     {self.dns.rootserver.router_id}')

class DNSDaemon(Daemon):
    def __init__(self, root: Zone) -> None:
        self.routers_to_zones: dict[Router, list[Zone]] = {}
        self.add_root_tree(root)

    def add_router(self, router: Router) -> None:
        self.routers_to_zones[router] = []
        return super().add_router(router)

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
    ) -> None:
        self.name = name
        self.parent = parent
        self.server = server
        self.children: list[Zone] = []

    def add_child(self, zone: Zone):
        self.children.append(zone)

    def get_full_name(self) -> str:
        if self.parent is not None:
            return self.name + "." + self.parent.get_full_name()
        else:
            return self.name
