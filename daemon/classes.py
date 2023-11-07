from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from topology.classes import Router, Topology


class Daemon(ABC):
    def add_router(self, router: Router) -> None:
        router.add_daemon(self)

    @abstractmethod
    def get_configurer(self) -> DaemonConfigurer:
        pass


class DaemonConfigurer(ABC):
    daemon_type: type[Daemon]

    @abstractmethod
    def configure(self, router: Router, path: Path):
        pass


class DaemonParser(ABC):
    def __init__(self, path: Path) -> None:
        self.data = self.load(path)

    @abstractmethod
    def load(self, path: Path) -> Any:
        pass

    @abstractmethod
    def merge(self, topology: Topology):
        pass
