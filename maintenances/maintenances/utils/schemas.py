import ipaddress
import socket
import subprocess
from typing import Literal, Optional

from pydantic import BaseModel, validator

_JIRA_PROJECTS_LIST = [
    "COR",
    "SYS",
    "DEV",
    "NOC",
    "ISO",
    "CEN",
]


class BaseYAML(BaseModel):

    ticket: str
    hostname: str
    device_type: Literal["iosxr", "junos"]

    @staticmethod
    def ping_test(host):
        """Run subprocess ping to verify hostname is valid.

        output == 0 if ping succeeds.
        """
        output = subprocess.run(
            ["ping", "-c", "1", "-t", "1", "-n", host], stdout=subprocess.DEVNULL
        )
        assert output.returncode == 0, f"Invalid hostname {host}"

    @validator("ticket")
    def check_tickets_all(cls, v):
        """Validate Jira ticket."""
        error_msg = f"{v} must be a valid ticket number."
        assert v[:3] in _JIRA_PROJECTS_LIST, error_msg
        assert v[3] == "-", error_msg
        assert v[4:].isdigit(), error_msg
        return v

    @validator("hostname")
    def check_hostname(cls, v):
        """Check reachability."""
        BaseYAML.ping_test(v)
        return v


class MigrationsSchema(BaseYAML):
    folder_id: str
    sheet_title: str


class DevicesSchema(BaseYAML):
    """Schema for Devices Snapshots."""

    pass


class Circuit(BaseModel):

    port: str
    cpe: Optional[str] = None
    clr: int
    v4_neighbor: Optional[ipaddress.IPv4Address] = None
    v6_neighbor: Optional[ipaddress.IPv6Address] = None

    @validator("cpe", pre=True)
    def check_cpe(cls, v):
        BaseYAML.ping_test(v)
        return v

    @validator("v4_neighbor", always=True)
    def v4_neighbor_ip(cls, v, values) -> str:
        """Get IPv4 neighbor IP from cpe hostname if CPE set
        and no neighbor addresses defined."""
        if values["cpe"] and not values.get("v4_neighbor"):
            try:
                return socket.gethostbyname(values["cpe"])
            except KeyError:
                pass
        else:
            return v

    @validator("v6_neighbor", always=True)
    def v6_neighbor_ip(cls, v, values) -> str:
        """Get IPv4 neighbor IP from cpe hostname if CPE set
        and no neighbor addresses defined."""
        if values["cpe"] and not values.get("v6_neighbor"):
            try:
                return socket.getaddrinfo(
                    values["cpe"], 22, socket.AF_INET6, 0, socket.IPPROTO_TCP
                )[0][-1][0]
            except KeyError:
                pass
        else:
            return v


class CircuitsSchema(BaseYAML):
    """Schema for Circuits Snapshots."""

    global_router: Optional[str]
    circuits: list[Circuit]

    @validator("global_router")
    def check_global_router(cls, v, values):
        if values["device_type"] == "iosxr":
            BaseYAML.ping_test(v)
            return socket.gethostbyname(v)
