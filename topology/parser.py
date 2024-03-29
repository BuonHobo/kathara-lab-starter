from pathlib import Path
import json
from typing import Any
from topology.classes import Router, Lan, Interface, Topology


def parse_json(path: Path):
    with path.open("r") as l:
        return json.load(l)


def parse_topology(topology: dict[str, Any]) -> Topology:
    lans: dict[str, str] = topology["lans"]
    parsed_lans: dict[str, Lan] = {
        name: Lan(name.upper(), full_address) for name, full_address in lans.items()
    }
    routers: dict[str, dict[str, str]] = topology["routers"]
    defaults: dict[str, list[str]] = (
        topology["defaults"] if "defaults" in topology else {}
    )
    result: Topology = Topology()

    for name, interfaces in routers.items():
        router = Router(name)

        for interface_name, interface_data in interfaces.items():
            split_data = interface_data.split()
            byte = split_data[0]
            lan = parsed_lans[split_data[1].upper()]
            Interface(interface_name, byte, lan, router)

        result.add_router(router)

    for line in defaults:
        client, deflt = [word.strip() for word in line.split()]
        client_rtr: Router = result.get_router_by_name(client)
        deflt_rtr = result.get_router_by_name(deflt)
        client_rtr.set_default_router(deflt_rtr)

    return result


def get_topology(path: Path) -> Topology:
    return parse_topology(parse_json(path))
