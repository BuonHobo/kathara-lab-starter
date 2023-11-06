from pathlib import Path
from typing import Any
import json
from daemon.classes import DaemonParser
from daemon.ospf.classes import OSPF, Area, Cost
from topology.classes import Lan, Router, Topology


class OSPFParser(DaemonParser):
    @staticmethod
    def load(path: Path) -> Any:
        with path.open("r") as l:
            return json.load(l)

    def merge(self, topology: Topology):
        areas: dict[str, dict[str, str]] = self.data["areas"]
        stubs: dict[str, str] = areas["stubs"]
        backbones: dict[str, str] = areas["backbones"]
        parsed_lans: dict[str, Lan] = topology.get_lan_map()
        parsed_routers = topology.get_router_map()
        routers: list[str] = self.data["routers"]

        result = OSPF()

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
