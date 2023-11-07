from __future__ import annotations
from pathlib import Path
from daemon.classes import Daemon, DaemonConfigurer
from topology.classes import Interface, Lan, Router


class OSPFConfigurer(DaemonConfigurer):
    def __init__(self, daemon: OSPF) -> None:
        self.daemon: OSPF = daemon

    def configure(self, router: Router, path: Path):
        lines: list[str] = []
        for cost in self.daemon.costs[router]:
            lines.append(f"interface {cost.interface.name}\n")
            lines.append(f"ospf cost {cost.value}\n")

        lines.append("router ospf\n")
        for lan in router.get_lans():
            if lan in self.daemon.lans:
                area = self.daemon.lans[lan]
                lines.append(f"network {lan.full_address} area {area.name}\n")
                if area.is_stub:
                    lines.append(f"area {area.name} stub\n")
        lines.append("redistribute connected\n")

        path = path.joinpath("etc/frr/")

        with path.joinpath("frr.conf").open("a") as f:
            f.writelines(lines)

        with path.joinpath("daemons").open("a") as f:
            f.write("\nospfd=yes")


class OSPF(Daemon):
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
