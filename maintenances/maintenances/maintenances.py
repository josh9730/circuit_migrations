import json
import sys
from datetime import datetime
from enum import Enum
from pprint import pprint

import typer
import yaml
from dictdiffer import diff
from lib import getters
from pydantic import ValidationError
from utils import logins, schemas

"""
Notes:
    - Does not fully support VRFs
    - Optimizations possible with XR 7+ (i.e. native get_route_to)
    - Optics getters?
    - Static route support?
    - arbitrary route checks?
    - Junos migrations tested?
"""


maintenances = typer.Typer(
    add_completion=False,
    help="""
Maintenance functions per-device and per-circuit.

Snapshots:
- Circuit: Get interesting info by circuit, including BGP Path Attributes. Outputs json file, diff-able.
- Device: Get interesting info by device. Outputs json file, diff-able.

Migrations:
- Get interesting info by device, push to GSheet (using pandas). Similar to Device Snapshots.
""",
)


class SnapshotsOptions(str, Enum):
    device = "device"
    circuit = "circuit"

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
    """Pull full device data and upload to GSheets.
    Originally intended for device migrations.
    """
    data = open_validate_input(schemas.MigrationsSchema)
    getter = getters.Main(data)
    getter.get_migration_data_full()


@maintenances.command()
def snapshots(
    snapshots_type: SnapshotsOptions = typer.Argument(
        ..., help="Circuits or Device checks"
    ),
    diffs: bool = typer.Option(False, "--diffs", "-d", help="Do diffs and print"),
    jira: bool = typer.Option(
        False, "--jira", "-j", help="Upload snapshots output to ticket"
    ),
):
    """Pull snapshots by Device or Circuit. Intended for either the full Device or by
    attached Circuit, to be used as pre- and post-maintenance verifications.
    """
    snapshots_schema = SnapshotsOptions.return_schema(snapshots_type)
    data = open_validate_input(snapshots_schema)

    getter = getters.Main(data)

    # run PMs
    if snapshots_type == "device":
        output = getter.devices_pms()
    elif snapshots_type == "circuit":
        output = getter.circuits_pms()

    # write outputs, perform diffs if requested
    base_filename = (
        f'{data["hostname"]}_{snapshots_type}_{datetime.today().strftime("%Y-%m-%d")}_'
    )
    if diffs:
        pre_json = None
        filename = base_filename + "post.json"
        try:
            with open("outputs/" + base_filename + "pre.json", "r") as f:
                pre_json = json.load(f)

        except FileNotFoundError:
            print(f"Expected pre-maintenance file '{base_filename}pre.json' not found.")

            while not pre_json:
                input_filename = input("Supply correct pre- filename for diffs: ")
                try:
                    with open("outputs/" + input_filename, "r") as f:
                        pre_json = json.load(f)
                except FileNotFoundError:
                    pass

        finally:
            print(f'Writing output to {filename}')
            with open("outputs/" + filename, "w") as f:
                json.dump(output, f, indent=2)

        if pre_json:
            diffs = list(diff(pre_json, output))
            print("\n", "-" * 10, "DIFFS", "-" * 10, "\n")
            pprint(diffs, indent=2)
            print("\n", "-" * 10, "END DIFFS", "-" * 10, "\n")

            print(f'Writing diffs to {filename}')
            with open("outputs/" + base_filename + "diffs.json", "w") as f:
                json.dump(diffs, f, indent=2)

    else:
        filename = base_filename + "pre.json"
        print(f'Writing output to {filename}')
        with open("outputs/" + filename, "w") as f:
            json.dump(output, f, indent=2)

    if jira:
        jira = logins.Login().jira_login()
        print(f'Uploading {filename} to {data["ticket"]}.')
        jira.add_attachment(data['ticket'], 'output/' + filename)


if __name__ == "__main__":
    maintenances()

# fre-agg4_circuit_2022-04-19_pre.json
