import time
import socket
import pandas as pd

from utils.logins import Login
from utils.gsheets import GSheets
from lib import parsers


class Main:
    def __init__(self, data):
        self.hostname = socket.gethostbyname(
            data["hostname"]
        )  # using hostname breaks on XR
        self.data = data
        self.device_type = data["device_type"]
        self.logins = Login()

        self.start_time = time.time()
        self.napalm_connection = self.logins.napalm_connect(
            self.hostname, self.device_type
        )
        self.napalm_connection.open()

    def _interface_common_getters(self, extra_inputs: tuple) -> dict:
        """Return inputs and collapse onto ifaces_all. Meant to be used
        for common getters to migrations and device_pms.

        Dict of interfaces is returned.
        """
        ifaces_all = self.napalm_connection.get_interfaces()
        ip_ifaces = parsers.format_ip_int(self.napalm_connection.get_interfaces_ip())
        mpls = self.napalm_connection.get_mpls_interfaces_custom()
        isis = self.napalm_connection.get_isis_interfaces_custom()
        arp = self.napalm_connection.get_arp_table_custom()
        nd = self.napalm_connection.get_nd_table_custom()

        for i in (ip_ifaces, ip_ifaces, mpls, isis, arp, nd, *extra_inputs):
            {ifaces_all[k].update(v) for (k, v) in i.items() if ifaces_all.get(k)}

        for i in ifaces_all:
            if not ifaces_all[i].get("mpls_enabled"):
                ifaces_all[i].update({"mpls_enabled": False})

        return ifaces_all

    def get_migration_data_full(self):
        """Return outputs for Device-wide planning.
        Typically for planning router refreshes, not tested on Junos.
        """
        optics = self.napalm_connection.get_optics_inventory_custom()
        interfaces_all = self._interface_common_getters((optics,))

        bgp = parsers.format_bgp_detail(
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
        interfaces, bgp_missing_int = parsers.collapse_bgp(interfaces, bgp)

        # create DataFrames for pushing to GSheets
        interfaces_df = pd.DataFrame.from_dict(interfaces, orient="index")
        interfaces_df["interfaces"] = interfaces_df.index
        interfaces_df = parsers.sort_df_circuits_columns(interfaces_df)
        bgp_missing_df = pd.DataFrame.from_dict(bgp_missing_int, orient="index")
        GSheets(self.data).dump_circuits_all(interfaces_df, bgp_missing_df)

    def devices_pms(self) -> dict:
        """Dumps JSON of Device-specific outputs for PMs.

        optics???
        """
        iface_counters = self.napalm_connection.get_interfaces_counters()
        interfaces_all = self._interface_common_getters((iface_counters,))

        bgp = self.napalm_connection.get_bgp_neighbors_detail()
        if not self.device_type == "junos":  # junos has custom getter
            bgp = parsers.format_bgp_detail(bgp)

        msdp = self.napalm_connection.get_msdp_neighbrs_custom()
        pim = self.napalm_connection.get_pim_neighbors_custom()
        software = self.napalm_connection.get_facts()["os_version"]

        self.napalm_connection.close()

        # collapse bgp onto interfaces
        interfaces, bgp_missing_int = parsers.collapse_bgp(interfaces_all, bgp)

        output = {
            "Software": software,
            "Non-Port BGP": bgp_missing_int,
            "MSDP": msdp,
            "PIM": pim,
            "Interfaces": interfaces,
        }
        return output

    def circuits_pms(self) -> dict:
        """Uses Napalm to get all data except BGP route detail. Multiple
        custom getters are defined (and override in some cases).

        Uses full device custom getters from Device PMs for convienence.
        """
        iface_counters = self.napalm_connection.get_interfaces_counters()
        interfaces_all = self._interface_common_getters((iface_counters,))

        output_dict = {}
        for counter, circuit in enumerate(self.data["circuits"]):
            circuit_data = interfaces_all[circuit["port"]]
            clr = f'CLR-{circuit["clr"]}'
            output_dict.update(
                {
                    clr: {
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

            # iBGP, v4/6_neighbor added during schema validation
            if circuit_data.get("isis_state"):
                output_dict[clr].update(
                    {
                        "IS-IS": {
                            "Neighbor": circuit_data["isis_neighbor"],
                            "NH": circuit_data["isis_nh"],
                            "Metric": circuit_data["isis_metric"],
                            "MPLS": circuit_data["mpls_enabled"],
                        }
                    }
                )

            # eBGP, static?
            else:
                circuit["v4_neighbor"] = circuit_data.get("arp_nh")
                circuit["v6_neighbor"] = circuit_data.get("nd_nh")

            # 'get_bgp_neighbor_routes' for Junos is able to retrieve both the
            # list of routes like the XR getter, as well as all other needed
            # information, eliminating the need for another get-route-to call.
            if self.device_type == "junos":
                routes_dict = {}
                if circuit["v4_neighbor"]:
                    routes_dict.update(
                        self.napalm_connection.get_bgp_neighbor_routes(
                            circuit["v4_neighbor"]
                        )
                    )
                if circuit["v6_neighbor"]:
                    routes_dict.update(
                        self.napalm_connection.get_bgp_neighbor_routes(
                            circuit["v6_neighbor"]
                        )
                    )

            # Non-Junos uses a Junos 'global' router to get the routes data
            # The 'get_bgp_neighbor_routes for non-Junos returns a list of routes
            # (via an XR CLI command) and then passes this list to a custom.
            # Junos 'get-route-to' getter
            else:
                routes_list = []
                if circuit["v4_neighbor"]:
                    routes_list.append(
                        self.napalm_connection.get_bgp_neighbor_routes(
                            circuit["v4_neighbor"]
                        )
                    )
                if circuit["v6_neighbor"]:
                    routes_list.append(
                        self.napalm_connection.get_bgp_neighbor_routes(
                            circuit["v6_neighbor"]
                        )
                    )

                # reset OTP for new napalm connection
                if counter == 0:
                    elapsed_time = time.time() - self.start_time
                    if elapsed_time < 30:
                        time.sleep(30 - elapsed_time)
                    self.juniper_connection = self.logins.napalm_connect(
                        self.data["global_router"], "junos"
                    )
                    self.juniper_connection.open()

                routes_dict = self.juniper_connection.get_route_to(routes_list)
            output_dict[clr].update({"BGP": routes_dict})

        self.napalm_connection.close()
        try:
            self.juniper_connection.close()
        except AttributeError:
            pass

        return output_dict
