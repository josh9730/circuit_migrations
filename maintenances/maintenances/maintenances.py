import sys
import yaml
import json
import typer
from datetime import datetime
from pprint import pprint
from enum import Enum
from pydantic import ValidationError

from utils import schemas
from lib import cisco, juniper

"""
Pending:
    - Validating input in data.yaml fully
    - fix otp re-attempt
    - mock testing
    - napalm compliance testing



    - re-do logins with decorator?
    - support for routing instances
    - support for MPLS, eline, elan, IPVPN?
"""

maintenances = typer.Typer(
    add_completion=False,
    help="""
Maintenance functions
""",
)


class SnapshotsOptions(str, Enum):
    devices = "devices"
    circuits = "circuits"

    @classmethod
    def return_schema(cls, snapshots_type):
        if snapshots_type == "devices":
            return schemas.DevicesSchema
        else:
            return schemas.CircuitsSchema


def open_validate_input(model) -> dict:
    """Open YAML, validate, and return output dict."""
    with open("data.yaml") as f:
        data = yaml.safe_load(f)

    try:
        data = model(**data)
        return data.dict()
    except ValidationError as e:
        sys.exit(e)


@maintenances.command()
def migrations():
    """Pull stuff"""
    data = open_validate_input(schemas.MigrationsSchema)
    if data["device_type"] == "iosxr":
        device_getter = cisco.Main(data)
        device_getter.get_migration_data_full()
    elif data["device_type"] == "junos":
        print('Not currently supported.')


@maintenances.command()
def snapshots(
    snapshots_type: SnapshotsOptions = typer.Argument(
        ..., help="Circuits or Device checks"
    ),
    diffs: bool = typer.Option(False, help="Do Diffs and print"),
    jira: bool = typer.Option(False, help="Upload snapshots output to ticket"),
):
    snapshots_schema = SnapshotsOptions.return_schema(snapshots_type)
    data = open_validate_input(snapshots_schema)

    # initialize connection
    if data["device_type"] == "iosxr":
        device_getter = cisco.Main(data)
    elif data["device_type"] == "junos":
        device_getter = juniper.Main(data)

    # run PMs
    if snapshots_type == "devices":
        output = device_getter.devices_pms()
    elif snapshots_type == "circuits":
        output = device_getter.circuits_pms()

    # write data
    filename = f'{data["hostname"]}_{datetime.today().strftime("%Y-%m-%d")}_'
    if diffs:
        filename = filename + "post.json"

    else:
        filename = "outputs/" + filename + "pre.json"
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)


if __name__ == "__main__":
    maintenances()
