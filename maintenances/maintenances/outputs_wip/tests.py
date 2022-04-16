import json
from pprint import pprint
import functools
import subprocess
import pygsheets
import pandas as pd
import socket
from copy import deepcopy

import ipaddress

import re

"""
jdickman@JD5099 outputs % python tests.py
Please go to this URL and finish the authentication flow: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=762168172204-06i0v6l2tl1hc32ls09lto77ssurvbj8.apps.googleusercontent.com&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&state=yVXYkCLYu9crIfQIP3qIFYHGObmOzP&prompt=consent&access_type=offline
Enter the authorization code: 4/1AX4XfWitD5xdq5EkfImcJgVVqm6H8ZTlthX9KAiBp_sDE3biIG54UvRQhd0
"""

# Add to yaml
# folder_id = "1CgYtqYFZy5M3WfgpYGu0exBF6FERulwu"  # default to None
# sheet_title = "CSAC MX10K Migration"


# df = pd.read_json("comb_dict2.json", orient="index")
# df2 = pd.read_json("bgp_missing_int.json", orient="index")

# with open("outputs_circuits_ifaces.json", "r") as f:
#     data = json.load(f)

# iface = 'GigabitEthernet100/0/0/11'
# parsed_iface = re.match(r'([^\d]*)(\d.*)', iface).groups()[1]
# print(parsed_iface)

# new_dict = {}

# data_keys = list(data.keys())
# for i in data_keys:
#     print(i)
#     if parsed_iface in i:
#         new_iface = i

# new_dict.update({
#     new_iface: data[new_iface]
# })

# pprint(new_dict)


# for k, v in bgp.items():
#     ip_type = next(iter(v['address_family'].keys()))

#     for asn, peer_list in bgp_detail['global'].items():
#         if asn == v['remote_as']:

# bgp_new.update(
#     {
#         k: {
#             'local_as': v['local_as'],
#             'remote_as': v['remote_as'],
#             'description': v['description'],
#             'is_enabled': v['is_enabled'],
#             'is_up': v['is_up'],
#             f'{ip_type}_received_prefixes': v['address_family'][ip_type]['received_prefixes'],
#             f'{ip_type}_accepted_prefixes': v['address_family'][ip_type]['accepted_prefixes'],
#             f'{ip_type}_sent_prefixes': v['address_family'][ip_type]['sent_prefixes'],

#         }
#     }
# )
# pprint(bgp_new)
# exit(1)


# print(df.to_dict(orient='records')[0])


# df['interfaces'] = df.index

# df = df[
#     [
#         'interfaces',
#         "description",
#         "speed",
#         "mtu",
#         "is_enabled",
#         "is_up",
#         "optic",
#         "optic_serial",
#         "mac_address",
#         "ipv4_address",
#         "ipv6_address",
#         "isis_neighbor",
#         "isis_state",
#         "isis_nh",
#         "isis_ipv6",
#         "arp_nh",
#         "arp_nh_mac",
#         "nd_nh",
#         "nd_mac",
#         "local_as",
#         "remote_as",
#         "remote_id",
#         "ipv4_rx_prefixes",
#         "ipv4_acpt_prefixes",
#         "ipv4_tx_prefixes",
#         "ipv4_bgp_uptime",
#         "ipv6_rx_prefixes",
#         "ipv6_acpt_prefixes",
#         "ipv6_tx_prefixes",
#         "ipv6_bgp_uptime",
#     ]
# ]

# b = a.at['Bundle-Ether5.326', 'ipv4']

# print(a['ipv4'].keys())


# df.drop(columns=['ipv4'], inplace=True)


# df1 = pd.json_normalize(iface_dict)
# # first_n_column  = df.iloc[: , :5]
# df1 = df.head(5)
# # pprint(df1)

# # pprint(first_n_column)


# client = pygsheets.authorize()

# try:
#     sht = client.open(sheet_title)

# except pygsheets.SpreadsheetNotFound:
#     print(f"\nSheet not found, creating sheet titled: {sheet_title}")
#     sht = client.create(sheet_title, folder=folder_id)


# try:
#     circuits_sheet = sht.worksheet_by_title("circuits")
#     bgp_sheet = sht.worksheet_by_title("bgp")

# except pygsheets.exceptions.WorksheetNotFound:
#     # will error if one of above exists
#     circuits_sheet = sht.add_worksheet("circuits")
#     bgp_sheet = sht.add_worksheet("bgp")
#     sht.del_worksheet(sht.worksheet_by_title("Sheet1"))

# circuits_sheet.clear()
# circuits_sheet.set_dataframe(df, start=(1, 1), extend=True, nan="")

# bgp_sheet.clear()
# bgp_sheet.set_dataframe(df2, start=(1, 1), extend=True, nan="")

neighbors_rib = [
    (
        "bgp.rtarget.0",
        [
            ("received_prefix_count", 89),
            ("accepted_prefix_count", 89),
            ("advertised_prefix_count", 1),
        ],
    ),
    (
        "inet.0",
        [
            ("received_prefix_count", 880749),
            ("accepted_prefix_count", 880749),
            ("advertised_prefix_count", 1),
        ],
    ),
    (
        "inet.2",
        [
            ("received_prefix_count", 1806),
            ("accepted_prefix_count", 1806),
            ("advertised_prefix_count", 0),
        ],
    ),
    (
        "bgp.l3vpn.0",
        [
            ("received_prefix_count", 0),
            ("accepted_prefix_count", 0),
            ("advertised_prefix_count", None),
        ],
    ),
    (
        "bgp.l3vpn.2",
        [
            ("received_prefix_count", 0),
            ("accepted_prefix_count", 0),
            ("advertised_prefix_count", None),
        ],
    ),
    (
        "bgp.l3vpn-inet6.0",
        [
            ("received_prefix_count", 0),
            ("accepted_prefix_count", 0),
            ("advertised_prefix_count", None),
        ],
    ),
    (
        "bgp.l3vpn-inet6.2",
        [
            ("received_prefix_count", 0),
            ("accepted_prefix_count", 0),
            ("advertised_prefix_count", None),
        ],
    ),
    (
        "bgp.evpn.0",
        [
            ("received_prefix_count", 0),
            ("accepted_prefix_count", 0),
            ("advertised_prefix_count", 0),
        ],
    ),
    (
        "bgp.mvpn.0",
        [
            ("received_prefix_count", 0),
            ("accepted_prefix_count", 0),
            ("advertised_prefix_count", 0),
        ],
    ),
    (
        "bgp.mvpn-inet6.0",
        [
            ("received_prefix_count", 0),
            ("accepted_prefix_count", 0),
            ("advertised_prefix_count", 0),
        ],
    ),
]
neighbor_details = {}
for rib_table in neighbors_rib:
    # pprint(rib_table)
    print(rib_table[0])

    print(dict(rib_table[1]))
    neighbor_details.update({rib_table[0]: dict(rib_table[1])})

pprint(neighbor_details)