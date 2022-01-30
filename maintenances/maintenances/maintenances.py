"""
Pending:
    - Validating input in data.yaml fully

"""


import yaml
import argparse

from utils.checks import data_checks
from lib.devices import *


def main(args):
    with open("data.yaml") as f:
        data = yaml.safe_load(f)

    # check yaml against schema
    data_checks(data)

    if args.circuit_data:
        device_type = data['device_type']

        if device_type == "iosxr":
            circuit_data = MigrationInfoXR(data)
            circuit_data.get_interfaces()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Maintenance functions")
    parser.add_argument(
        "-c",
        "--circuit_data",
        action="store_true",
        help="Return circuit data for migration prep",
    )
    args = parser.parse_args()

    main(args)
