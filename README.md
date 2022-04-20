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