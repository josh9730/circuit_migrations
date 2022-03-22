import subprocess
from typing import Literal
from pydantic import (
    BaseModel,
    validator,
)


class BaseYAML(BaseModel):

    ticket: str
    hostname: str
    device_type: Literal['iosxr', 'junos']

    @validator("ticket")
    def check_tickets_all(cls, ticket):
        """Validate Jira ticket."""
        error_msg = f"{ticket} must be a valid ticket number."
        # assert ticket[:3] in JIRA_PROJECTS_LIST, error_msg -- get list of projects
        assert ticket[3] == "-", error_msg
        assert ticket[4:].isdigit(), error_msg
        return ticket

    @validator("hostname")
    def check_hostname(cls, hostname):
        """Validate hostname, must be pingable.

        output == 0 if ping succeeds.
        """
        output = subprocess.run(['ping', '-c', '1', '-t', '1', '-n', hostname], stdout=subprocess.DEVNULL)
        assert output.returncode == 0, f'Invalid hostname {hostname}'
        return hostname
