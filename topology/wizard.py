from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
from pathlib import Path
from daemon.ospf.parser import add_ospf
from topology.classes import Router, Topology
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


def initialize_root(config, folder, topology):
    for router in topology.routers:
        path = folder.joinpath(router.name)
        path.mkdir()
        copy_tree(config.joinpath("etc").as_posix(), path.joinpath("etc").as_posix())


def configure_daemons(folder, topology):
    for router in topology.routers:
        for daemon in router.daemons:
            daemon.configurer.configure(router, daemon, folder.joinpath(router.name))


def configure_topology(config: Path, folder: Path):
    topology: Topology = get_topology(config)
    make_lab_conf(folder, topology)
    make_startup_files(folder, topology)
    initialize_root(config, folder, topology)

    if config.joinpath("ospf.yaml").exists():
        add_ospf(config, topology)

    configure_daemons(folder, topology)
