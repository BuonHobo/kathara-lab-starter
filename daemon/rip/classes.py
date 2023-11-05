from pathlib import Path
from daemon.classes import Daemon, DaemonConfigurer
from topology.classes import Router


class RIPConfigurer(DaemonConfigurer):
    @staticmethod
    def configure(router: Router, daemon: Daemon, path: Path):
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
    configurer: type[RIPConfigurer] = RIPConfigurer
