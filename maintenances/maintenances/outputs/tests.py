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


# a = pd.read_json("comb_dict.json", orient='index')
# b = a.at['Bundle-Ether5.326', 'ipv4']

# print(a['ipv4'].keys())


with open("bgp.json", "r") as f:
    bgp_dict = json.load(f)

with open("comb_dict2.json", "r") as f:
    iface_dict = json.load(f)

bgp_peers = bgp_dict["global"]["peers"]

for iface in iface_dict:
    v4_neighbor, v6_neighbor = None, None

    # iBGP
    if iface_dict[iface].get("IS-IS Neighbor"):
        isis_neighbor = iface_dict[iface]["IS-IS Neighbor"]
        v4_neighbor = socket.gethostbyname(isis_neighbor)
        try:
            socket.getaddrinfo(
                isis_neighbor, None, socket.AF_INET6, socket.SOCK_DGRAM
            )[0][-1][0]
        except IndexError:
            print(f"{iface_dict} has no IPv6 Neighbor.")

    # eBGP
    elif iface_dict[iface].get("ARP NH"):
        v4_neighbor = iface_dict[iface]["ARP NH"]
        if iface_dict[iface].get("ND NH"):
            v6_neighbor = iface_dict[iface]["ND NH"]

    # update interface dict with BGP keys
    if v4_neighbor and bgp_peers.get(v4_neighbor):
        path = bgp_peers[v4_neighbor]['address_family']['ipv4']
        bgp_peers[v4_neighbor].update(
            {
                'ipv4_rx_prefixes': path['received_prefixes'],
                'ipv4_acpt_prefixes': path['accepted_prefixes'],
                'ipv4_tx_prefixes': path['sent_prefixes'],
            }
        )
        bgp_peers[v4_neighbor].pop('address_family')
        iface_dict[iface].update(bgp_peers[v4_neighbor])

        # remove matched peer, un-matched will be dumped to a second sheet
        bgp_peers.pop(v4_neighbor, None)

    if v6_neighbor and bgp_peers.get(v6_neighbor):
        path = bgp_peers[v6_neighbor]['address_family']['ipv6']
        iface_dict[iface].update(
            {
                'ipv6_rx_prefixes': path['received_prefixes'],
                'ipv6_acpt_prefixes': path['accepted_prefixes'],
                'ipv6_tx_prefixes': path['sent_prefixes'],
            }
        )

        # remove matched peer, un-matched will be dumped to a second sheet
        bgp_peers.pop(v6_neighbor, None)

pprint(iface_dict)


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
# circuits_sheet.set_dataframe(df, start=(1, 2), extend=True, nan="")
