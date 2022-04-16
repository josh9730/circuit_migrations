import logging
import netaddr
from copy import deepcopy
from napalm.junos.junos import JunOSDriver
from jnpr.junos.exception import RpcError

from custom_napalm.utils import junos_cust_views

log = logging.getLogger(__file__)


class CustomJunOSDriver(JunOSDriver):
    """Extends base JunOSDriver for custom methods."""

    def rpc_get(self, rpc_input, msg):
        try:
            return rpc_input.get()
        except RpcError as rpcerr:
            log.error(f"Unable to retrieve {msg} information:")
            log.error(str(rpcerr))
            return {}

    def get_isis_interfaces_custom(self) -> dict:
        """Via PyEZ, return dict of ISIS interfaces

        {{ Interface }}: {
            isis_neighbor: system-id
            isis_state: bool
            isis_next-hop: ipaddress
            isis_ipv6: bool
            isis_metric: int
        }
        """
        rpc_adj = junos_cust_views.ISISAdjacencyTable(self.device)
        isis_adjacencies = self.rpc_get(rpc_adj, "IS-IS neighbors").items()
        rpc_int = junos_cust_views.ISISInterfaceTable(self.device)
        isis_interfaces = self.rpc_get(rpc_int, "IS-IS neighbors").items()

        # convert int_results to dict
        int_dict = {}
        for interface in isis_interfaces:
            int_dict.update({interface[0][0]: interface[1][0][1]})

        # create return dict
        isis = {}
        for neighbor in isis_adjacencies:
            isis.update(
                {
                    neighbor[0][0]: {
                        "isis_neighbor": neighbor[1][0][1],
                        "isis_state": neighbor[1][1][1],
                        "isis_nh": neighbor[1][3][1],
                        "isis_ipv6": neighbor[1][2][1],
                        "isis_metric": int(int_dict[neighbor[0][0]]),
                    }
                }
            )
        return isis

    def get_mpls_interfaces_custom(self) -> dict:
        """Via PyEZ, return dict of MPLS-enabled interfaces.

        {{ Interface }}: {
            mpls_enabled: bool
        }
        """
        rpc = junos_cust_views.MPLSInterfaceTable(self.device)
        mpls_interfaces = self.rpc_get(rpc, "MPLS Interfaces").items()

        # create return dict
        mpls = {}
        for port in mpls_interfaces:
            mpls.update({port[0][0]: {"mpls_enabled": port[1][0][1]}})
        return mpls

    def get_msdp_neighbrs_custom(self) -> list:
        """Via PyEZ, return list of MSDP neighbors.

        [
            {{ Neighbor IP }}
        ]
        """
        rpc = junos_cust_views.MSDPNeighborTable(self.device)
        return self.rpc_get(rpc, "MSDP Neighbors").keys()

    def get_pim_neighbors_custom(self) -> list:
        """Via PyEZ, return list of PIM neighbors.

        [
            {{ PIM Interface }}
        ]
        """
        rpc = junos_cust_views.PIMNeighborTable(self.device)
        return self.rpc_get(rpc, "PIM Interfaces").keys()

    def get_arp_table_custom(self) -> dict:
        """Via PyEZ, return dict of ARP table.

        {{ Interface }}: {
            arp_nh
            arp_nh_mac
        }

        MAC is normalized using EUI format.
        """
        rpc = junos_cust_views.ARPTable(self.device)
        arp_table = self.rpc_get(rpc, "ARP").items()

        arp = {}
        for neighbor in arp_table:
            try:
                mac = str(netaddr.EUI(neighbor[1][1][1])).replace("-", ":")
            except netaddr.core.AddrFormatError:
                mac = None
            arp.update(
                {
                    neighbor[0]: {
                        "arp_nh_mac": mac,
                        "arp_nh": neighbor[1][0][1],
                    }
                }
            )
        return arp

    def get_nd_table_custom(self) -> dict:
        """Via PyEZ, return dict of ND table.

        {{ Interface }}: {
            nd_nh
            nd_nh_mac
        }

        MAC is normalized using EUI format.
        """
        rpc = junos_cust_views.NDTable(self.device)
        nd_table = self.rpc_get(rpc, "IPv6 ND").items()

        nd = {}
        for neighbor in nd_table:
            try:
                mac = str(netaddr.EUI(neighbor[1][1][1])).replace("-", ":")
            except netaddr.core.AddrFormatError:
                mac = None
            nd.update(
                {
                    neighbor[0]: {
                        "nd_nh": neighbor[1][0][1],
                        "nd_nh_mac": mac,
                    }
                }
            )
        return nd

    def get_bgp_neighbors_detail(self) -> dict:
        """Via PyEz, return custom BGP Neighbors Detail.

        Differences between hardware/software versions. Default Napalm getter
        expects peer-address, local-address, local-as, remote-as to be directly
        under the 'bgp-peer' element. On some devices, those elements are instead
        nested under 'bgp-peer-header'. This getter accounts for both.

        The Napalm getter also aggregated the rib counts. This getter returns a
        nested dict by routing table instead.
        """
        rpc = junos_cust_views.junos_bgp_neighbors_table(self.device)
        neighbor_data = self.rpc_get(rpc, "BGP Neighbors").items()

        default_neighbor_details = {
            "up": False,
            "local_as": 0,
            "remote_as": 0,
            "router_id": "",
            "local_address": "",
            "routing_table": "",
            "import_policy": "",
            "export_policy": "",
        }

        bgp_detail = {}
        for neighbor in neighbor_data:
            neighbor_details = deepcopy(default_neighbor_details)
            neighbor_details.update(
                {elem[0]: elem[1] for elem in neighbor[1] if elem[1] is not None}
            )

            # remove one of local_as or local_as_2, etc
            for i in ["local_as", "remote_as"]:
                if not neighbor_details[i]:
                    neighbor_details[i] = neighbor_details.pop(f"{i}_2")
                else:
                    neighbor_details.pop(f"{i}_2")

            # remove ports from address field if present
            neighbor_details["local_address"] = neighbor_details["local_address"].split(
                "+"
            )[0]
            neighbors_rib = neighbor_details.pop("rib").items()

            # append rib tables, will return nested dicts of tables
            for rib_table in neighbors_rib:
                neighbor_details.update({rib_table[0]: dict(rib_table[1])})
            bgp_detail.update({neighbor[0].split("+")[0]: neighbor_details})
        return bgp_detail
