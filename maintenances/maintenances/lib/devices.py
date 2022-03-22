from napalm.base.exceptions import ConnectionException
import time
import json
import subprocess
import socket

from utils.logins import Login
from utils.gsheets import GSheets


import pandas as pd

#
# IOS-XR
#


class IOSXRMain:
    """Getter for IOS-XR devices (ASR-9010)"""

    def __init__(self, data):
        self.hostname = socket.gethostbyname(
            data["hostname"]
        )  # using hostname breaks on XR
        self.device_type = data["device_type"]
        self.data = data
        logins = Login()

        # # retry login once if MFA fails
        # for i in range(2):
        #     try:
        #         # self.napalm_connection = logins.napalm_connect(self.hostname, self.device_type)
        #     except ConnectionException:
        #         print("\n\nWaiting ~30 seconds for OTP to reset\n")
        #         time.sleep(30)
        #         continue

        self.napalm_connection = logins.napalm_connect(self.hostname, self.device_type)
        # self.napalm_connection = logins.napalm_connect_test()
        self.napalm_connection.open()

        alive = self.napalm_connection.is_alive()
        if not alive:
            raise ConnectionException(
                "\n\nConnection not established, wait 30s and re-try.\n"
            )

    def collapse_bgp(self, iface_dict, bgp_dict):
        """Collapse BGP dictionary onto the consolidated interface dictionary.

        BGP peerings matched with Interface by ARP/ND neighbors. Once a peering
        is matched with an interface, the BGP dict is popped, allowing the peerings
        not associated with an interface to be returned later.
        """
        bgp_peers = bgp_dict["global"]["peers"]

        for iface in iface_dict:
            v4_neighbor, v6_neighbor = None, None

            # iBGP
            if iface_dict[iface].get("isis_neighbor"):
                isis_neighbor = iface_dict[iface]["isis_neighbor"]
                v4_neighbor = socket.gethostbyname(isis_neighbor)
                try:
                    v6_neighbor = socket.getaddrinfo(
                        isis_neighbor, None, socket.AF_INET6, socket.SOCK_DGRAM
                    )[0][-1][0]
                except IndexError:
                    print(f"{iface_dict} has no IPv6 Neighbor.")

            # eBGP
            elif iface_dict[iface].get("arp_nh"):
                v4_neighbor = iface_dict[iface]["arp_nh"]
                if iface_dict[iface].get("nd_nh"):
                    v6_neighbor = iface_dict[iface]["nd_nh"]

            # update interface dict with BGP keys
            if v4_neighbor and bgp_peers.get(v4_neighbor):
                path = bgp_peers[v4_neighbor]['address_family']['ipv4']
                bgp_peers[v4_neighbor].update(
                    {
                        'ipv4_rx_prefixes': path['received_prefixes'],
                        'ipv4_acpt_prefixes': path['accepted_prefixes'],
                        'ipv4_tx_prefixes': path['sent_prefixes'],
                        'ipv4_bgp_uptime': bgp_peers[v4_neighbor]['uptime'],
                    }
                )
                bgp_peers[v4_neighbor].pop('address_family')
                bgp_peers[v4_neighbor].pop('uptime')
                bgp_peers[v4_neighbor].pop('description')
                iface_dict[iface].update(bgp_peers[v4_neighbor])

                # remove matched peer, un-matched will be dumped to a second sheet
                bgp_peers.pop(v4_neighbor, None)

            if v6_neighbor and bgp_peers.get(v6_neighbor):
                path = bgp_peers[v6_neighbor]['address_family']['ipv6']
                bgp_peers[v6_neighbor].update(
                    {
                        'ipv6_rx_prefixes': path['received_prefixes'],
                        'ipv6_acpt_prefixes': path['accepted_prefixes'],
                        'ipv6_tx_prefixes': path['sent_prefixes'],
                        'ipv6_bgp_uptime': bgp_peers[v6_neighbor]['uptime'],
                    }
                )
                bgp_peers[v6_neighbor].pop('address_family')
                bgp_peers[v6_neighbor].pop('uptime')
                bgp_peers[v6_neighbor].pop('description')
                iface_dict[iface].update(bgp_peers[v6_neighbor])

                # remove matched peer, un-matched will be dumped to a second sheet
                bgp_peers.pop(v6_neighbor, None)
        return bgp_peers

    def format_ip_int(self, data: dict):
        """Collapse napalm ip interface output to:

        {
            {{ INT }}:
                ipv4_address: {{ IP }},
                ipv6_address: {{ IP }}
        }
        """
        output = {}
        for k, v in data.items():
            ip_dict = {}
            for i in range(4, 7, 2):
                ip = v.get(f"ipv{i}")
                if ip:
                    address = next(iter(ip))
                    ip_dict.update(
                        {f"ipv{i}_address": f"{address}/{ip[address]['prefix_length']}"}
                    )

            output.update({k: ip_dict})
        return output

    def get_migration_data_full(self):
        """Return outputs for Device-wide planning.

        Typically for planning router refreshes
        """
        interfaces_all = self.napalm_connection.get_interfaces()
        ip_interfaces = self.format_ip_int(self.napalm_connection.get_interfaces_ip())
        optics = self.napalm_connection.get_optics_inventory()
        isis = self.napalm_connection.get_isis_neighbors()
        arp = self.napalm_connection.get_arp_table()
        nd = self.napalm_connection.get_ipv6_nd()
        bgp = self.napalm_connection.get_bgp_neighbors()

        # remove un-needed interfaces
        interfaces = {}
        for iface in interfaces_all.keys():
            if not iface.startswith(("Mgmt", "Null", "nVFab", "Loop", "PTP")) and (
                interfaces_all[iface]["is_enabled"] or interfaces_all[iface]["is_up"]
            ):
                interfaces.update({iface: interfaces_all[iface]})

        # collapse onto interfaces
        for i in [ip_interfaces, optics, isis, arp, nd]:
            {interfaces[k].update(v) for (k, v) in i.items() if interfaces.get(k)}
        bgp_missing_int = self.collapse_bgp(interfaces, bgp)

        # with open("outputs/comb_dict2.json", "w") as f:
        #     json.dump(interfaces, f, indent=2)

        # with open('outputs/bgp_missing_int.json', 'w') as f:
        #     json.dump(bgp_missing_int, f, indent=2)

        self.napalm_connection.close()

        GSheets(self.data).dump_circuits_all(interfaces, bgp_missing_int)


class MigrationInfoXR(IOSXRMain):
    """ """

    pass


# class DeviceXR(IOSXR):
#     """Device-specific methods"""

#     pass


#
# Junos
#


class Junos:
    """Getter for Juniper MX Devices."""

    pass


class CircuitJunos(Junos):
    pass


class DeviceJunos(Junos):
    pass
