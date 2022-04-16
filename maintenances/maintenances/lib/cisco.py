import time
import socket
import ipaddress
import pandas as pd
from napalm.base.exceptions import ConnectionException

from utils.logins import Login
from utils.gsheets import GSheets
from lib import parsers




# change PIM, MSDP to lists of IPs
# make match format of Juniper
# EUI for ND






class Main:
    """Getter for IOS-XR devices (ASR-9010)"""

    def __init__(self, data: dict):
        self.hostname = socket.gethostbyname(
            data["hostname"]
        )  # using hostname breaks on XR
        self.data = data
        self.logins = Login()
        self.start_time = time.time()

        self.napalm_connection = self.logins.napalm_connect(self.hostname, "iosxr")
        self.napalm_connection.open()

        if not self.napalm_connection.is_alive():
            raise ConnectionException(
                "\n\nConnection not established, wait 30s and re-try.\n"
            )

    def interface_common_getters(self, extra_inputs: tuple) -> dict:
        """Return inputs and collapse onto ifaces_all. Meant to be used
        for common getters to migrations and device_pms.

        Dict of interfaces is returned.
        """
        ifaces_all = self.napalm_connection.get_interfaces()
        ip_ifaces = parsers.format_ip_int(self.napalm_connection.get_interfaces_ip())
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
        bgp = parsers.format_bgp_detail(
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

    def circuits_global_bgp(self, circuit: dict, routes_list: list) -> dict:
        """Per-Circuit BGP data."""
        routes_dict = {}
        for route in routes_list:
            if isinstance(ipaddress.ip_network(route), ipaddress.IPv4Network):
                table = "inet.0"
            else:
                table = "inet6.0"

            route_data = self.juniper_connection.get_route_to(
                destination=route, protocol="bgp"
            )
            route_parsed = parsers.parse_junos_bgp_routes(route_data, table, route)
            routes_dict.update(route_parsed)
        return routes_dict

    def circuits_pms(self) -> dict:
        """Uses Napalm XR to get all data except BGP route detail.
        Napalm Junos (to 'global' router) used to get BGP PAs due to
        poor support on XR.

        Uses full device custom getters from Device PMs for convienence.
        """
        start_time = time.time()
        iface_counters = self.napalm_connection.get_interfaces_counters()
        interfaces_all = self.interface_common_getters((iface_counters,))

        output_dict = {}
        for counter, circuit in enumerate(self.data["circuits"]):
            circuit_data = interfaces_all[circuit["port"]]
            output_dict.update(
                {
                    circuit["clr"]: {
                        "Interface": {
                            "Name": circuit["port"],
                            "Description": circuit_data["description"],
                            "is_enabled": circuit_data["is_enabled"],
                            "is_up": circuit_data["is_up"],
                            "mac_address": circuit_data["mac_address"],
                            "mtu": circuit_data["mtu"],
                            "ipv4_address": circuit_data["ipv4_address"],
                            "ipv6_address": circuit_data.get("ipv6_address"),
                            "Counters": {
                                "TX Errors": circuit_data["tx_errors"],
                                "TX Discards": circuit_data["tx_discards"],
                                "RX Errors": circuit_data["rx_errors"],
                                "RX Discards": circuit_data["rx_discards"],
                            },
                        },
                        "ARP/ND": {
                            "arp_nh": circuit_data["arp_nh"],
                            "arp_nh_mac": circuit_data["arp_nh_mac"],
                            "nd_nh": circuit_data.get("nd_nh"),
                            "nd_mac": circuit_data.get("nd_mac"),
                        },
                    }
                }
            )

            # iBGP
            if circuit_data.get("isis_state"):
                output_dict[circuit["clr"]].update(
                    {
                        "IS-IS": {
                            "Neighbor": circuit_data["isis_neighbor"],
                            "NH": circuit_data["isis_nh"],
                            "Metric": circuit_data["isis_metric"],
                        }
                    }
                )

            # eBGP, static?
            else:
                circuit["v4_neighbor"] = circuit_data.get("arp_nh")
                circuit["v6_neighbor"] = circuit_data.get("nd_nh")

            if circuit["v4_neighbor"]:
                routes_list = self.napalm_connection.get_bgp_neighbor_routes(
                    circuit["v4_neighbor"]
                )
            if circuit["v6_neighbor"]:
                routes_list_v6 = self.napalm_connection.get_bgp_neighbor_routes(
                    circuit["v6_neighbor"]
                )
                if routes_list_v6:
                    routes_list.append(routes_list_v6)

            # if first loop, sleep and login to global_router
            if counter == 0:
                elapsed_time = time.time() - start_time
                if elapsed_time < 30:
                    time.sleep(30 - elapsed_time)
                self.juniper_connection = self.logins.napalm_connect(
                    self.data["global_router"], "junos"
                )
                self.juniper_connection.open()

            routes_dict = self.circuits_global_bgp(circuit, routes_list)
            output_dict[circuit["clr"]].update({"BGP": routes_dict})

        self.napalm_connection.close()
        self.juniper_connection.close()
        return output_dict
