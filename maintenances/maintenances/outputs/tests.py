import json
from pprint import pprint
import functools
import subprocess
import pygsheets
import pandas as pd
import socket



"""
jdickman@JD5099 outputs % python tests.py
Please go to this URL and finish the authentication flow: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=762168172204-06i0v6l2tl1hc32ls09lto77ssurvbj8.apps.googleusercontent.com&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&state=yVXYkCLYu9crIfQIP3qIFYHGObmOzP&prompt=consent&access_type=offline
Enter the authorization code: 4/1AX4XfWitD5xdq5EkfImcJgVVqm6H8ZTlthX9KAiBp_sDE3biIG54UvRQhd0
"""

# Add to yaml
folder_id = "1CgYtqYFZy5M3WfgpYGu0exBF6FERulwu"  # default to None
sheet_title = "CSAC MX10K Migration"


df = pd.read_json("comb_dict2.json", orient="index")
# df2 = pd.read_json("bgp_missing_int.json", orient="index")

with open('bgp_missing_int.json', 'r') as f:
    bgp = json.load(f)

# df2 = pd.json_normalize(bgp)


for k, v in bgp.items():
    if v['address_family'].get('ipv4'):
        path = v['address_family']['ipv4']
    else:
        path = v['address_family']['ipv6']

    bgp[k].update(
        {
            'received_prefixes': path['received_prefixes'],
            'accepted_prefixes': path['accepted_prefixes'],
            'sent_prefixes': path['sent_prefixes'],
        }
    )
    bgp[k].pop('address_family')



df2 = pd.DataFrame.from_dict(bgp, orient='index')
print(df2)
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

