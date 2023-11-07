from __future__ import annotations
from pathlib import Path
from daemon.classes import Daemon, DaemonConfigurer
from topology.classes import Router


class RIPConfigurer(DaemonConfigurer):
    def __init__(self, daemon: RIP) -> None:
        self.daemon = daemon

    def configure(self, router: Router, path: Path):
        lines: list[str] = []

        lines.append("router rip\n")
        for lan in router.get_lans():
            lines.append(f"network {lan.full_address}\n")
        lines.append("redistribute connected\n")

        path = path.joinpath("etc/frr/")

        with path.joinpath("frr.conf").open("a") as f:
            f.writelines(lines)

        with path.joinpath("daemons").open("a") as f:
            f.write("\nripd=yes")


class RIP(Daemon):
    def __init__(self) -> None:
        self.configurer = RIPConfigurer(self)

    def get_configurer(self) -> DaemonConfigurer:
        return self.configurer
