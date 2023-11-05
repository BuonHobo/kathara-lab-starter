from pathlib import Path
from typing import Any
import yaml
from daemon.classes import DaemonParser
from daemon.rip.classes import RIP
from topology.classes import Router, Topology


class RIPParser(DaemonParser):
    @staticmethod
    def load(path: Path) -> Any:
        with path.open("r") as l:
            return yaml.load(l.read(), yaml.Loader)

    def merge(self, topology: Topology):
        routers: list[str] = self.data["routers"]

        parsed_routers = topology.get_router_map()

        result = RIP()

        for router in routers:
            result.add_router(parsed_routers[router])
