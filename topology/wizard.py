import shutil
from pathlib import Path
from daemon.dns.parser import DNSParser
from daemon.frr.frr import FRR
from topology.classes import Topology
from topology.parser import get_topology


def make_lab_conf(folder: Path, topology: Topology):
    lines: list[str] = []
    for router in topology.routers:
        for interface in router.interfaces.values():
            lines.append(f"{router.name}[{interface.number}]={interface.lan.name}\n")
        lines.append("\n")
    with folder.joinpath("lab.conf").open("w") as file:
        file.writelines(lines)


def make_startup_files(folder: Path, topology: Topology):
    for router in topology.routers:
        lines: list[str] = []
        for interface in router.interfaces.values():
            lines.append(f"ip a add {interface.full_address} dev {interface.name}\n")
        if router.default_router is not None:
            d_r =router.default_router
            for iface in router.get_neighbors():
                if iface.router is d_r:
                    lines.append(f"ip route add default via {iface.address}\n")
        with folder.joinpath(f"{router.name}.startup").open("w") as file:
            file.writelines(lines)


def initialize_root(config: Path, folder: Path, topology: Topology):
    for router in topology.routers:
        path = folder.joinpath(router.name)
        path.mkdir()


def configure_daemons(folder: Path, data: Path, topology: Topology):
    for router in topology.routers:
        for daemon in router.daemons:
            daemon.get_configurer().configure(
                router, folder.joinpath(router.name), data
            )


def configure_topology(config: Path, target: Path, data: Path = Path("data")):
    if target.exists():
        shutil.rmtree(target.as_posix())
    target.mkdir()

    topology: Topology = get_topology(config.joinpath("topology.json"))
    make_lab_conf(target, topology)
    make_startup_files(target, topology)
    initialize_root(config, target, topology)

    FRR(config, topology)
    if config.joinpath("dns.json").exists():
        DNSParser(config.joinpath("dns.json")).merge(topology)

    configure_daemons(target, data, topology)
