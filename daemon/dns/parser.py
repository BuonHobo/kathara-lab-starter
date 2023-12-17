from collections import defaultdict
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

    @staticmethod
    def get_name() -> str:
        return "dns"

    def zone_tree(
        self,
        parent: Zone,
        zone_name_to_server: dict[str, Router],
        zone_name_to_name: dict[str, list[Router]],
        data: list[str] | dict[str, Any],
    ) -> None:
        for zone in data:
            names: list[Router] = []
            if zone in zone_name_to_name:
                names = zone_name_to_name[zone]
            if type(data) == list:
                parent.add_child(Zone(zone, parent, zone_name_to_server[zone], names))
            elif type(data) == dict:
                data = data
                current = Zone(zone, parent, zone_name_to_server[zone], names)
                parent.add_child(current)
                self.zone_tree(
                    current, zone_name_to_server, zone_name_to_name, data[zone]
                )

    def merge(self, topology: Topology):
        server_lines: list[str] = self.data["servers"]
        name_to_router = topology.get_router_map()
        zone_name_to_server: dict[str, Router] = {}
        for line in server_lines:
            zone_name, server_name = line.split()
            zone_name_to_server[zone_name] = name_to_router[server_name]

        zone_name_to_name: dict[str, list[Router]] = defaultdict(list)
        if "names" in self.data:
            name_lines: list[str] = self.data["names"]
            for line in name_lines:
                router_name, zone_name = line.split()
                rtr = topology.get_router_by_name(router_name)
                if rtr is None:
                    raise ValueError(f"{router_name} does not exist")
                zone_name_to_name[zone_name].append(rtr)

        root = Zone("", None, zone_name_to_server["root"], zone_name_to_name["root"])
        self.zone_tree(root, zone_name_to_server, zone_name_to_name, self.data["root"])

        dns = DNSDaemon(root)

        if "resolvers" in self.data:
            resolver_lines = self.data["resolvers"]
            for line in resolver_lines:
                lst: list[str] = line.split()
                res = lst.pop(0)
                resolver = topology.get_router_by_name(res)
                clients: list[Router | None] = [
                    topology.get_router_by_name(router) for router in lst
                ]

                if resolver is None:
                    raise ValueError(f"the router {res} does not exist")
                dns.add_resolver(resolver)

                for client in clients:
                    if client is None:
                        raise ValueError(
                            f"the router specified as client does not exist"
                        )
                    dns.add_client(client, resolver)
