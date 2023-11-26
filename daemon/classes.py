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
    @abstractmethod
    def configure(self, router: Router, path: Path, data: Path):
        pass


class DaemonParser(ABC):
    def __init__(self, path: Path) -> None:
        self.data = self.load(path)
        self.daemon = self.init_daemon()

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @abstractmethod
    def load(self, path: Path) -> Any:
        pass

    @abstractmethod
    def merge(self, topology: Topology):
        pass

    def get_daemon(self) -> Daemon:
        return self.daemon

    def init_daemon(self) -> Daemon:
        return self.get_daemon_type()()

    @abstractmethod
    def get_daemon_type(self) -> type[Daemon]:
        pass
