from __future__ import annotations
from abc import abstractmethod
from collections import defaultdict
from pathlib import Path
from daemon.classes import Daemon, DaemonConfigurer, DaemonParser
from topology.classes import Router, Topology
from shutil import copytree
from topology.classes import Interface, Lan, Router
from typing import Any
import json


class FRRConfigurer(DaemonConfigurer):
    def __init__(self, daemon: FRR) -> None:
        self.daemon = daemon

    def configure(self, router: Router, path: Path, data: Path):
        # enables frr on that computer
        with path.parent.joinpath(router.name + ".startup").open("a") as f:
            f.write("\nsystemctl start frr\n")
        # copies /etc/frr in that computer's root
        path.joinpath("etc").mkdir()
        copytree(data.joinpath("frr"), path.joinpath("etc/frr"))
        # configures all required daemons
        for daemon in self.daemon.router_to_daemons[router]:
            daemon.get_configurer().configure(router, path, data)


class FRR(Daemon):
    def __init__(self, config: Path, topology: Topology) -> None:
        self.configurer: FRRConfigurer = FRRConfigurer(self)
        self.router_to_daemons: dict[Router, list[Daemon]] = defaultdict(list)
        self.configure_daemons(config, topology)

    def get_configurer(self) -> DaemonConfigurer:
        return self.configurer

    def add_daemon_to_router(self, daemon: Daemon, router: Router):
        if router not in self.router_to_daemons:
            self.add_router(router)
        self.router_to_daemons[router].append(daemon)

    def configure_daemons(self, config: Path, topology: Topology):
        for daemon in (OSPFParser, RIPParser, BGPParser):
            conf_path = config.joinpath(f"{daemon.get_name()}.json")
            if conf_path.exists():
                parser = daemon(conf_path, self)
                parser.merge(topology)


class FRRDaemon(Daemon):
    def setFRR(self, frr: FRR):
        self.frr = frr

    def add_router(self, router: Router) -> None:
        self.frr.add_daemon_to_router(self, router)


class FRRParser(DaemonParser):
    def __init__(self, path: Path, frr: FRR) -> None:
        self.frr = frr
        self.daemon = self.init_daemon()
        super().__init__(path)

    def init_daemon(self) -> Daemon:
        daemon: FRRDaemon = self.get_daemon_type()()  # type:ignore
        daemon.setFRR(self.frr)
        return daemon

    def get_daemon(self) -> Daemon:
        return self.daemon

    @abstractmethod
    def get_daemon_type(self) -> type[Daemon]:
        pass


class RIPParser(FRRParser):
    def load(self, path: Path) -> Any:
        with path.open("r") as l:
            return json.load(l)

    def merge(self, topology: Topology):
        routers: list[str] = self.data["routers"]

        parsed_routers = topology.get_router_map()

        result = self.get_daemon()

        for router in routers:
            result.add_router(parsed_routers[router])

    @staticmethod
    def get_name() -> str:
        return "rip"

    def get_daemon_type(self) -> type[Daemon]:
        return RIP


class RIPConfigurer(DaemonConfigurer):
    def __init__(self, daemon: RIP) -> None:
        self.daemon = daemon

    def configure(self, router: Router, path: Path, data: Path):
        lines: list[str] = []

        lines.append("router rip\n")
        for lan in router.get_lans():
            lines.append(f"network {lan.full_address}\n")
        lines.append("redistribute connected\n\n")

        path = path.joinpath("etc/frr/")

        with path.joinpath("frr.conf").open("a") as f:
            f.writelines(lines)

        with path.joinpath("daemons").open("a") as f:
            f.write("\nripd=yes")


class RIP(FRRDaemon):
    def __init__(self) -> None:
        super().__init__()
        self.configurer = RIPConfigurer(self)

    def get_configurer(self) -> DaemonConfigurer:
        return self.configurer


class OSPFParser(FRRParser):
    def load(self, path: Path) -> Any:
        with path.open("r") as l:
            return json.load(l)

    def merge(self, topology: Topology):
        areas: dict[str, dict[str, str]] = self.data["areas"]
        stubs: dict[str, str] = areas["stubs"] if "stubs" in areas else {}
        backbones: dict[str, str] = areas["backbones"]
        parsed_lans: dict[str, Lan] = topology.get_lan_map()
        parsed_routers = topology.get_router_map()
        routers: list[str] = self.data["routers"]

        result = self.get_ospf()

        for name, lans in stubs.items():
            stub = Area(name, True)
            for lan in lans.split():
                stub.add_lan(parsed_lans[lan])
            result.add_area(stub)

        for name, lans in backbones.items():
            backbone = Area(name, False)
            for lan in lans.split():
                backbone.add_lan(parsed_lans[lan])
            result.add_area(backbone)

        for router in routers:
            result.add_router(parsed_routers[router])

        costs: list[str] = self.data["costs"]
        for cost in costs:
            router, interface, value = cost.split()
            router = parsed_routers[router]
            interface = router.get_interface(interface)
            result.add_cost(router, Cost(interface, value))

    @staticmethod
    def get_name() -> str:
        return "ospf"

    def get_daemon_type(self) -> type[Daemon]:
        return OSPF

    def get_ospf(self) -> OSPF:
        return self.get_daemon()  # type:ignore


class OSPFConfigurer(DaemonConfigurer):
    def __init__(self, daemon: OSPF) -> None:
        self.daemon: OSPF = daemon

    def configure(self, router: Router, path: Path, data: Path):
        lines: list[str] = []
        for cost in self.daemon.costs[router]:
            lines.append(f"interface {cost.interface.name}\n")
            lines.append(f"ospf cost {cost.value}\n\n")

        lines.append("router ospf\n")
        for lan in router.get_lans():
            if lan in self.daemon.lans:
                area = self.daemon.lans[lan]
                lines.append(f"network {lan.full_address} area {area.name}\n")
                if area.is_stub:
                    lines.append(f"area {area.name} stub\n")
        lines.append("redistribute connected\n\n")

        path = path.joinpath("etc/frr/")

        with path.joinpath("frr.conf").open("a") as f:
            f.writelines(lines)

        with path.joinpath("daemons").open("a") as f:
            f.write("\nospfd=yes")


class OSPF(FRRDaemon):
    def __init__(self) -> None:
        super().__init__()
        self.configurer: OSPFConfigurer = OSPFConfigurer(self)
        self.lans: dict[Lan, Area] = {}
        self.costs: dict[Router, list[Cost]] = {}

    def add_area(self, area: Area):
        for lan in area.lans:
            self.lans[lan] = area

    def add_router(self, router: Router):
        self.costs[router] = []
        return super().add_router(router)

    def add_cost(self, router: Router, cost: Cost):
        self.costs[router].append(cost)

    def get_configurer(self) -> DaemonConfigurer:
        return self.configurer


class Area:
    def __init__(self, name: str, is_stub: bool) -> None:
        self.name = name
        self.is_stub = is_stub
        self.lans: list[Lan] = []

    def add_lan(self, lan: Lan):
        self.lans.append(lan)


class Cost:
    def __init__(self, interface: Interface, value: str) -> None:
        self.interface = interface
        self.value = value


class BGP(FRRDaemon):  # Stores the bgp data
    def __init__(self) -> None:
        super().__init__()
        self.configurer = BGPConfigurer(self)
        # Init bgp specific data structures
        self.router_to_as: dict[Router, str] = {}
        self.as_to_router: dict[str, list[Router]] = defaultdict(list)

    def get_configurer(self) -> DaemonConfigurer:
        return self.configurer

    def add_as_router(self, as_name: str, router: Router) -> None:
        self.router_to_as[router] = as_name
        self.as_to_router[as_name].append(router)
        return super().add_router(router)


class BGPParser(FRRParser):  # Parses the bgp data
    def load(self, path: Path) -> Any:
        with path.open("r") as l:
            return json.load(l)

    @staticmethod
    def get_name() -> str:
        return "bgp"

    def get_daemon_type(self) -> type[Daemon]:
        return BGP

    def get_bgp(self) -> BGP:
        return self.get_daemon()  # type:ignore

    def merge(self, topology: Topology):
        ASes: list[str] = self.data["AS"]
        bgp = self.get_bgp()

        for line in ASes:
            line = line.split()
            ASn: str = line.pop(0)
            for router in line:
                r = topology.get_router_by_name(router)
                if r:
                    bgp.add_as_router(ASn, r)


class BGPConfigurer(DaemonConfigurer):  # Writes the bgp config
    def __init__(self, bgp: BGP) -> None:
        self.bgp = bgp

    def configure(self, router: Router, path: Path, data: Path):
        with path.joinpath("etc/frr/daemons").open("a") as f:
            f.write("\nbgpd=yes")

        lines: list[str] = []
        as_name = self.bgp.router_to_as[router]
        lines.append("""log file /var/log/frr/frr.log

debug bgp
debug bgp events
debug bgp filters
debug bgp fsm
debug bgp keepalives
debug bgp updates
                     
""")
        lines.append(f"router bgp {as_name}\n\n")
        lines.append(f"! no bgp ebgp-requires-policy\n")
        lines.append(f"! no bgp network import-check\n\n")

        vicini = [
            iface
            for iface in router.get_neighbors()
            if iface.router in self.bgp.router_to_as
        ]
        esterni = [
            iface for iface in vicini if self.bgp.router_to_as[iface.router] != as_name
        ]
        interni = [iface for iface in vicini if iface not in esterni]

        # aggiunge tutti i neighbors interni
        non_connessi = [
            r
            for r in self.bgp.as_to_router[as_name]
            if r not in (interface.router for interface in interni) and r is not router
        ]
        for rt in non_connessi:
            lines.append(
                f"neighbor <{rt.name} {rt.router_id}> remote-as {as_name}\n"
            )
            lines.append(
                f"neighbor <{rt.name} {rt.router_id}> description {rt.name}\n\n"
            )

        for iface in interni:
            lines.append(f"neighbor {iface.address} remote-as {as_name}\n")
            lines.append(
                f"neighbor {iface.address} description {iface.router.name}\n\n"
            )

        # aggiunge tutti i neighbors esterni
        for interface in esterni:
            if self.bgp.router_to_as[interface.router] != as_name:
                lines.append(
                    f"neighbor {interface.address} remote-as {self.bgp.router_to_as[interface.router]}\n"
                )
                lines.append(
                    f"neighbor {interface.address} description {interface.router.name}\n\n"
                )

        # aggiunge tutte le network
        for lan in router.get_lans():
            lines.append(f"network {lan.full_address}\n")

        with path.joinpath("etc/frr/frr.conf").open("a") as f:
            f.writelines(lines)
