from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from topology.classes import Router, Topology


class Daemon(ABC):
    configurer: DaemonConfigurer

    def add_router(self, router: Router):
        router.add_daemon(self)


class DaemonConfigurer(ABC):
    daemon_type: type[Daemon]

    @staticmethod
    @abstractmethod
    def configure(router: Router, daemon: Daemon, path: Path):
        pass


class DaemonParser(ABC):
    def __init__(self, path: Path) -> None:
        self.data = self.load(path)

    @staticmethod
    @abstractmethod
    def load(path: Path) -> Any:
        pass

    @abstractmethod
    def merge(self, topology: Topology):
        pass
