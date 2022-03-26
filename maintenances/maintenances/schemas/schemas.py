import subprocess
from typing import Literal
from pydantic import (
    BaseModel,
    validator,
)


class BaseYAML(BaseModel):

    ticket: str
    hostname: str
    device_type: Literal["iosxr", "junos"]

    @validator("ticket")
    def check_tickets_all(cls, ticket):
        """Validate Jira ticket."""
        error_msg = f"{ticket} must be a valid ticket number."
        # assert ticket[:3] in JIRA_PROJECTS_LIST, error_msg -- get list of projects
        assert ticket[3] == "-", error_msg
        assert ticket[4:].isdigit(), error_msg

    @validator("hostname")
    def ping_hostname(hostname):
        """Run subprocess ping to verify hostname is valid.

        output == 0 if ping succeeds.
        """
        output = subprocess.run(
            ["ping", "-c", "1", "-t", "1", "-n", hostname], stdout=subprocess.DEVNULL
        )
        assert output.returncode == 0, f"Invalid hostname {hostname}"


class MigrationsSchema(BaseYAML):
    folder_id: str
    sheet_title: str


class DevicesSchema(BaseYAML):
    """Schema for Devices Snapshots."""

    pass


class CircuitsSchema(BaseYAML):
    """Schema for Circuits Snapshots."""

    circuits: list

    # @validator("circuits")
    # def check_circuits(cls, circuits):
    #     for device, circuits_dict in circuits.items():
    #         BaseYAML.check_device_name(device)

    #         # much more shit to validate
