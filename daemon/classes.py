from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from topology.classes import Router


class Daemon(ABC):
    configurer: DaemonConfigurer

    @abstractmethod
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def add_router(self, router: Router):
        router.add_daemon(self)


class DaemonConfigurer(ABC):
    daemon_type: type[Daemon]

    @staticmethod
    @abstractmethod
    def configure(router: Router, daemon: Daemon, path: Path):
        pass
