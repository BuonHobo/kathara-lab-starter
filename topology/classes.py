from __future__ import annotations
import daemon.classes


class Lan:
    def __init__(self, name: str, full_address: str) -> None:
        self.name = name
        self.full_address = full_address
        self.address, _, self.netmask = full_address.partition("/")
        self.stripped_address = ".".join(self.address.split(".")[:-1])
        self.interfaces: list[Interface] = []

    def add_interface(self, inter: Interface):
        self.interfaces.append(inter)

    def __repr__(self) -> str:
        return f"({self.name}: {self.full_address})"


class Router:
    def __init__(self, name: str) -> None:
        self.interfaces: dict[str, Interface] = {}
        self.name = name
        self.daemons: list[daemon.classes.Daemon] = []
        self.router_id: str | None = None

    def add_interface(self, interface: Interface):
        self.interfaces[interface.name] = interface
        if self.router_id is None:
            self.router_id = interface.address
        else:
            self.router_id = max(self.router_id, interface.address)

    def add_daemon(self, daemon: daemon.classes.Daemon):
        self.daemons.append(daemon)

    def get_lans(self) -> list[Lan]:
        lans: list[Lan] = []
        for interface in self.interfaces.values():
            lans.append(interface.lan)
        return lans

    def get_interface(self, name: str) -> Interface:
        return self.interfaces[name]

    def get_neighbors(self) -> list[Interface]:
        res: list[Interface] = []
        for lan in self.get_lans():
            for interface in lan.interfaces:
                if interface.router is not self:
                    res.append(interface)
        return res

    def __repr__(self) -> str:
        interfaces = ""
        for interface in self.interfaces:
            interfaces += " " + str(interface)

        return f"({self.name}: [{self.interfaces}])"


class Interface:
    def __init__(self, name: str, byte: str, lan: Lan, router: Router) -> None:
        self.name = name
        self.number = name[-1]
        self.address = lan.stripped_address + "." + byte
        self.full_address = self.address + "/" + lan.netmask
        self.lan = lan
        self.router: Router = router
        router.add_interface(self)
        lan.add_interface(self)

    def add_router(self, router: Router):
        self.router = router

    def __repr__(self) -> str:
        return f"({self.name}: {self.full_address})"


class Topology:
    def __init__(self) -> None:
        self.routers: list[Router] = []

    def add_router(self, router: Router):
        self.routers.append(router)

    def get_lans(self) -> list[Lan]:
        lans: list[Lan] = []
        for router in self.routers:
            lans.extend(router.get_lans())
        return lans

    def get_lan_map(self) -> dict[str, Lan]:
        return {lan.name: lan for lan in self.get_lans()}

    def get_router_map(self) -> dict[str, Router]:
        return {router.name: router for router in self.routers}

    def get_router_by_name(self, name: str) -> Router | None:
        for router in self.routers:
            if router.name == name:
                return router
