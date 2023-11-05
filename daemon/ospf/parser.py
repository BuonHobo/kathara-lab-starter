from pathlib import Path
import yaml
from daemon.ospf.classes import OSPF, Area, Cost
from topology.classes import Lan, Router, Topology


def parse_yaml(path: Path):
    with path.open("r") as l:
        return yaml.load(l.read(), yaml.Loader)


def merge_ospf(topology: Topology, data):
    areas: dict[str, dict[str, str]] = data["areas"]
    stubs: dict[str, str] = areas["stubs"]
    backbones: dict[str, str] = areas["backbones"]
    parsed_lans: dict[str, Lan] = topology.get_lan_map()
    parsed_routers = topology.get_router_map()
    routers: list[str] = data["routers"]

    result = OSPF()

    parsed_stubs: list[Area] = []
    for name, lans in stubs.items():
        stub = Area(name, True)
        for lan in lans.split():
            stub.add_lan(parsed_lans[lan])
        result.add_area(stub)

    parsed_backbones: list[Area] = []
    for name, lans in backbones.items():
        backbone = Area(name, False)
        for lan in lans.split():
            backbone.add_lan(parsed_lans[lan])
        result.add_area(backbone)

    for router in routers:
        result.add_router(parsed_routers[router])

    costs: list[str] = data["costs"]
    for cost in costs:
        router, interface, value = cost.split()
        router = parsed_routers[router]
        interface = router.get_interface(interface)
        result.add_cost(router, Cost(interface, value))

    return result


def add_ospf(folder: Path, topology: Topology):
    merge_ospf(topology, parse_yaml(folder.joinpath("ospf.yaml")))
