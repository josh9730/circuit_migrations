import sys
import yaml
import typer
from pydantic import ValidationError

from schemas import schemas
from lib.devices import IOSXRMain

"""
Pending:
    - Validating input in data.yaml fully
    - fix otp re-attempt
    - mock testing
    - napalm compliance testing

"""

maintenances = typer.Typer(
    add_completion=False,
    help="""
Maintenance functions
"""
)


def validate_input(model, data: dict):
    try:
        model(**data)
    except ValidationError as e:
        sys.exit(e)


@maintenances.command()
def all_circuits():
    """Pull stuff
    """
    with open("data.yaml") as f:
        data = yaml.safe_load(f)

    validate_input(schemas.BaseYAML, data)

    device_type = data["device_type"]

    if device_type == "iosxr":
        circuit_data = IOSXRMain(data).get_migration_data_full()
        # circuit_data.get_interfaces()


@maintenances.command()
def snapshots():
    pass


if __name__ == "__main__":
    maintenances()
