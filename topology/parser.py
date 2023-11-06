from pathlib import Path
import json
from topology.classes import Router, Lan, Interface, Topology


def parse_yaml(path: Path):
    with path.open("r") as l:
        return json.load(l)


def parse_topology(topology)->Topology:
    lans: dict[str, str] = topology["lans"]
    parsed_lans: dict[str, Lan] = {
        name: Lan(name, full_address) for name, full_address in lans.items()
    }
    routers: dict[str, dict[str, str]] = topology["routers"]

    result: Topology = Topology()

    for name, interfaces in routers.items():
        router = Router(name)

        for interface_name, interface_data in interfaces.items():
            split_data = interface_data.split()
            byte = split_data[0]
            lan = parsed_lans[split_data[1]]
            interface: Interface = Interface(interface_name, byte, lan)
            router.add_interface(interface)

        result.add_router(router)

    return result


def get_topology(path: Path) -> Topology:
    return parse_topology(parse_yaml(path))