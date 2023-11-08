import json
from pathlib import Path
from typing import Any
from daemon.classes import DaemonParser
from daemon.dns.classes import DNSDaemon, Zone
from topology.classes import Router, Topology


class DNSParser(DaemonParser):
    def load(self, path: Path) -> Any:
        with path.open("r") as f:
            return json.load(f)

    def zone_tree(
        self,
        parent: Zone,
        zone_name_to_router: dict[str, Router],
        data: list[str] | dict[str, Any],
    ) -> None:
        for zone in data:
            if type(data) == list:
                parent.add_child(Zone(zone, parent, zone_name_to_router[zone]))
            elif type(data) == dict:
                data = data
                current = Zone(zone, parent, zone_name_to_router[zone])
                parent.add_child(current)
                self.zone_tree(current, zone_name_to_router, data[zone])

    def merge(self, topology: Topology):
        server_lines: list[str] = self.data["servers"]
        name_to_router = topology.get_router_map()
        zone_name_to_router: dict[str, Router] = {}
        for line in server_lines:
            zone_name, server_name = line.split()
            zone_name_to_router[zone_name] = name_to_router[server_name]

        root = Zone("", None, zone_name_to_router["root"])
        self.zone_tree(root, zone_name_to_router, self.data["root"])

        DNSDaemon(root)
