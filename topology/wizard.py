import shutil
from pathlib import Path
from daemon.ospf.parser import OSPFParser
from daemon.rip.parser import RIPParser
from topology.classes import Topology
from topology.parser import get_topology


def make_lab_conf(folder: Path, topology: Topology):
    lines: list[str] = []
    for router in topology.routers:
        for interface in router.interfaces.values():
            lines.append(f"{router.name}[{interface.number}]={interface.lan.name}\n")
    with folder.joinpath("lab.conf").open("w") as file:
        file.writelines(lines)


def make_startup_files(folder: Path, topology: Topology, frr: bool = True):
    for router in topology.routers:
        lines: list[str] = []
        for interface in router.interfaces.values():
            lines.append(f"ip a add {interface.full_address} dev {interface.name}\n")
        if frr:
            lines.append("systemctl start frr")
        with folder.joinpath(f"{router.name}.startup").open("w") as file:
            file.writelines(lines)


def initialize_root(config: Path, folder: Path, topology: Topology):
    for router in topology.routers:
        path = folder.joinpath(router.name)
        path.mkdir()
        shutil.copytree(
            config.joinpath("etc").as_posix(), path.joinpath("etc").as_posix()
        )


def configure_daemons(folder: Path, topology: Topology):
    for router in topology.routers:
        for daemon in router.daemons:
            daemon.get_configurer().configure(router, folder.joinpath(router.name))


def configure_topology(config: Path, folder: Path):
    if folder.exists():
        shutil.rmtree(folder.as_posix())
    folder.mkdir()
    topology: Topology = get_topology(config.joinpath("topology.json"))
    make_lab_conf(folder, topology)
    make_startup_files(folder, topology)
    initialize_root(config, folder, topology)

    if config.joinpath("ospf.yaml").exists():
        OSPFParser(config.joinpath("ospf.json")).merge(topology)

    if config.joinpath("rip.yaml").exists():
        RIPParser(config.joinpath("rip.json")).merge(topology)

    configure_daemons(folder, topology)
