import time
import re
import socket
import pandas as pd
from napalm.base.exceptions import ConnectionException

from utils.logins import Login
from utils.gsheets import GSheets
from lib import parsers

import json


class Main:
    """Getter for IOS-XR devices (ASR-9010)"""

    def __init__(self, data: dict):
        self.hostname = socket.gethostbyname(
            data["hostname"]
        )  # using hostname breaks on XR
        self.data = data
        logins = Login()
        self.start_time = time.time()

        # # retry login once if MFA fails
        # for i in range(2):
        #     try:
        #         # self.napalm_connection = logins.napalm_connect(self.hostname, self.device_type)
        #     except ConnectionException:
        #         print("\n\nWaiting ~30 seconds for OTP to reset\n")
        #         time.sleep(30)
        #         continue

        self.napalm_connection = logins.napalm_connect(self.hostname, "iosxr")
        # self.napalm_connection = logins.napalm_connect_test()
        self.napalm_connection.open()

        alive = self.napalm_connection.is_alive()
        if not alive:
            raise ConnectionException(
                "\n\nConnection not established, wait 30s and re-try.\n"
            )

    def interface_common_getters(self, extra_inputs: tuple) -> dict:
        """Return inputs and collapse onto ifaces_all. Meant to be used
        for common getters to migrations and device_pms.

        Dict of interfaces is returned.
        """
        ifaces_all = self.napalm_connection.get_interfaces()
        ip_ifaces = parsers.xr_format_ip_int(self.napalm_connection.get_interfaces_ip())
        mpls = self.napalm_connection.get_mpls_interfaces_xr()
        isis = self.napalm_connection.get_isis_neighbors_xr()
        arp = self.napalm_connection.get_arp_table_xr()
        nd = self.napalm_connection.get_ipv6_nd_xr()

        for i in (ip_ifaces, ip_ifaces, mpls, isis, arp, nd, *extra_inputs):
            {ifaces_all[k].update(v) for (k, v) in i.items() if ifaces_all.get(k)}
        return ifaces_all

    def get_migration_data_full(self):
        """Return outputs for Device-wide planning.
        Typically for planning router refreshes
        """
        optics = self.napalm_connection.get_optics_inventory_xr()
        interfaces_all = self.interface_common_getters((optics,))

        bgp = parsers.xr_format_bgp_detail(
            self.napalm_connection.get_bgp_neighbors_detail()
        )
        self.napalm_connection.close()

        # remove un-needed interfaces
        interfaces = {}
        for iface in interfaces_all.keys():
            if not iface.startswith(("Mgmt", "Null", "nVFab", "Loop", "PTP")) and (
                interfaces_all[iface]["is_enabled"] or interfaces_all[iface]["is_up"]
            ):
                interfaces.update({iface: interfaces_all[iface]})

        # collapse bgp onto interfaces
        interfaces, bgp_missing_int = parsers.xr_collapse_bgp(interfaces, bgp)

        # create DataFrames for pushing to GSheets
        interfaces_df = pd.DataFrame.from_dict(interfaces, orient="index")
        interfaces_df["interfaces"] = interfaces_df.index
        interfaces_df = parsers.xr_sort_df_circuits_columns(interfaces_df)
        bgp_missing_df = pd.DataFrame.from_dict(bgp_missing_int, orient="index")
        GSheets(self.data).dump_circuits_all(interfaces_df, bgp_missing_df)

    def devices_pms(self):
        """Dumps JSON of Device-specific outputs for PMs."""
        iface_counters = self.napalm_connection.get_interfaces_counters()
        interfaces_all = self.interface_common_getters((iface_counters,))

        software = self.napalm_connection.get_facts()["os_version"]
        bgp = parsers.xr_format_bgp_detail(
            self.napalm_connection.get_bgp_neighbors_detail()
        )
        msdp = self.napalm_connection.get_msdp_summary_xr()
        pim = self.napalm_connection.get_pim_neighbors_xr()
        self.napalm_connection.close()

        # collapse bgp onto interfaces
        interfaces, bgp_missing_int = parsers.xr_collapse_bgp(interfaces_all, bgp)

        output = {
            "Software": software,
            "Non-Port BGP": bgp,
            "MSDP": msdp,
            "PIM": pim,
            "Interfaces": interfaces_all,
        }
        return output

    def circuits_pms(self):
        """
        Service
        Interface
            Counters, IPs, ARP, ND, ISIS, MPLS
        BGP
            Peer, ASN
            adv. count, default bool
            rx. count
            rx. details
                - communities
                - as path
                - metric
                - LP
                - origin
        """

        # iface_counters = self.napalm_connection.get_interfaces_counters()
        # interfaces_all = self.interface_common_getters((iface_counters,))

        # with open('outputs_circuits_ifaces.json', 'w') as f:
        #     json.dump(interfaces_all, f, indent=2)

        for circuit in self.data['circuits']:
            print(circuit)

        # # reset OTP for junos login for routes lookup
        # time.sleep()

        # output = {

        # }        
        # with open('')