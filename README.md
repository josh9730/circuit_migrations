# Maintenances

This program is designed to automate device & circuit checks for better consistency on Junos and IOS-XR devices. 

Several functions are included:

- Migrations data:
    - Pull full device data (BGP, IS-IS, MSDP, PIM, Interfaces & Counters, MPLS)
    - Output to a Google Sheet
    - Designed for device migration planning
- Device Snapshots:
    - Pull full device data, similar to Migrations data, and save to a json file
    - This file can then be diffed against future snapshots (i.e. pre- and post-maintenance)
    - Designed for device maintenances
- Circuits Snapshots:
    - Pull data by circuit, similar to Device Snapshots except limited to user-defined circuits
    - Diffs can be performed similar to Device Snapshots
    - Designed for one or more circuit maintenances being performed on one device
    - More detailed BGP Path Attributes are fetched here, such as list of communities, AS Path, etc

# How Does It Work

- User login info (MFA & Jira) are required to be saved locally to your Mac's Keychain to be accessed by the program via the Keyring library
- The user requests are input to a YAML file (`data.yaml`), which is validated using Pydantic before running the program
- NAPALM is used for all 'getters' (data retrieval from devices)
    - Many custom getters have been written (in PyEZ for Junos and PyIOSXR for IOS-XR)
- pygsheets (and Pandas) are used to push Migration data to Google Sheets
- Optionally, diffs can be requested between subsequent runs of the program. The diffs are printed to the terminal as well as written to a file
- Optionally, for Snapshots, outputs can be uploaded to a specified Jira ticket

# Why Should I Use This

Two main reasons: Juniper and IOS-XR data is retrieved and presented equivalently, and data is represented in dictionary format, both of which allow for much easier validation of changes and visibility of data. Here is a sanitized example of the Circuits Snapshots:

```json
{
  "CLR-1234": {
    "Interface": {
      "Name": "Te0/0/2/0",
      "Description": "10G to Nowhere",
      "Enabled": true,
      "Up": true,
      "MTU": 1500,
      "Counters": {
        "TX Errors": 10,
        "TX Discards": 0,
        "RX Errors": 0,
        "RX Discards": 0
      },
      "IPv4/IPv6": {
        "MAC": "50:87:89:70:13:B7",
        "IPv4 Address": "1.1.1.1/31",
        "IPv6 Address": "",
        "DNS": "10g--cpe1--agg1",
        "ARP/ND": {
          "ARP Next-Hop": "1.1.1.2",
          "ARP NH MAC": "50:87:89:70:13:B7",
          "IPv6 ND Next-Hop": "",
          "ND NH MAC": "50:87:89:70:13:B7"
        }
      }
    },
    "IS-IS": {
      "Neighbor": "agg1",
      "NH": "1.1.1.2",
      "Metric": 100,
      "MPLS": true
    },
    "BGP": {
      "10.0.0.0/24": {
        "Next-Hop": "1.1.1.2",
        "Local Preference": 100,
        "AS-Path": "100 200",
        "MED": 0,
        "Communities": [
          "100:100",
          "200:200"
        ]
      }
    }
  }
}
```

The Device Snapshots output is similar. Migrations pulls are similar to Device Snapshots except no json file is generated, instead data is pushed to a Google Sheets.

# How to Install

This program is packaged via Poetry, and can be installed via pip using the provided wheel (under `dist`), or you can clone this repo. 

# How to Perform Initial Setup

1. Verify python installation of 3.9 or higher
3. Configure [keyring](https://pypi.org/project/keyring/)
    - `keyring set {{ account }} {{ username }}`
        - password prompt
    - You must have the following:
        - `keyring set jira url {{ URL }}`
        - `keyring set mfa {{ USERNAME }}`
        - `keyring set otp {{ USERNAME }}`
            - otp is the MFA token for otp generation

### Google API Setup (optional, only for Migrations function)

1. Pending...

# How to Use the Input File

All user input is written in the `data.yaml` file under the main folder. No changes need to be made to any python files. Please review [HERE](https://www.w3schools.io/file/yaml-introduction/) for YAML tutorials if necessary.

Validation will be done on your YAML file upon running the program based on the type of function requested. For example, requesting a Migrations pull requires the `folder_id` variable, but this is not required for any of the other functions.

```yaml
ticket: 
hostname: 
device_type:

# Migrations, pygsheets vars
folder_id: 
sheet_title:

# Circuits Data
global_router:
circuits:
  - port:
    cpe:
    clr:
    v4_neighbor:
    v6_neighbor:
```

Always Required
1. `ticket`: Ticket number for Jira upload. Must be in {{ PROJECT }}-{{ KEY }} format. If not using Jira, enter in any value, such as `NOC-123456`.
2. `hostname`: Must be a reachable hostname or IP, this will be checked during YAML validation.
3. `device_type`: Must be `iosxr` or `junos`. Other device types are not supported at this time.

For Migrations
4. `folder_id`: Required for Migrations. This is the identifier of the folder you want to use, which is the string after `drive.google.com/drive/u/0/folders/` when navigating to this folder.
5. `sheet_title`: Required for Migrations. Title of the Google Sheet being used. Use an existing sheet's title if you want to overwrite.

For Circuits Snapshots:
6. `global_router`: This is only required for IOS-XR Circuit Snapshots, can be left blank if Junos. Must be a reachable hostname or IP, this will be checked during YAML validation.
7. `circuits`: List of dictionaries, only required for Circuits Snapshots
8. `port`: Required field. This must be the literal port name of the circuit you want to check.
1. `cpe`: Hostname (or IP) of the CPE, required if this is an iBGP connection (cannot get the BGP info from the port IPs if iBGP).
1. `clr`: Required field. Integer identifier of the circuit ID.
1. `v4_neighbor`: Optional field. For BGP, neighbor IPs are retrieved from ARP or from the A record, which may either fail or return a non-BGP-speaking IP. Set this field to override if needed.
1. `v6_neighbor`: Optional field. For BGP, neighbor IPs are retrieved from IPv6 ND or from the AAAA record, which may either fail or return a non-BGP-speaking IP. Set this field to override if needed.

# How to Run the Program

The program can be launched from `maintenances.py`.

[Typer](https://typer.tiangolo.com) is used as the command-line interface. `--help` can be used to walk through the available arguments and view help text.