from napalm.iosxr.iosxr import IOSXRDriver
import napalm.base.helpers
import copy
import textfsm
import tempfile
import re
from lxml import etree as ETREE
from netaddr import EUI

from . import textfsm_optics, textfsm_nd


class CustomIOSXRDriver(IOSXRDriver):
    """Extends base IOSXRDriver for custom methods"""

    def get_pim_neighbors_xr(self):
        """Returns list of PIM-enabled interfaces."""
        pim_neighbors = []
        pim_rpc_request = "<Get><Operational><PIM><Active><DefaultContext><NeighborSummaryTable>\
        </NeighborSummaryTable></DefaultContext></Active></PIM></Operational></Get>"

        pim_rpc_rply = ETREE.fromstring(self.device.make_rpc_call(pim_rpc_request))

        for interfaces in pim_rpc_rply.xpath(".//NeighborSummaryTable/NeighborSummary"):
            interface = napalm.base.helpers.find_txt(interfaces, "Naming/InterfaceName")
            pim_neighbors.append(interface)
        return pim_neighbors

    def get_msdp_summary_xr(self):
        """Returns dict of MSDP peerings keyed by peer IP."""
        msdp_peers = {}
        msdp_rpc_request = "<Get><Operational><MSDP><Active><DefaultContext><PeerSummaryTable>\
        </PeerSummaryTable></DefaultContext></Active></MSDP></Operational></Get>"
        msdp_rpc_reply = ETREE.fromstring(self.device.make_rpc_call(msdp_rpc_request))

        for peers in msdp_rpc_reply.xpath(
            ".//Active/DefaultContext/PeerSummaryTable/PeerSummary"
        ):
            peer = napalm.base.helpers.find_txt(peers, "Naming/PeerAddress")
            asn = napalm.base.helpers.find_txt(peers, "ASNumberString")

            msdp_peers.update({peer: asn})
        return msdp_peers

    def get_mpls_interfaces_xr(self):
        """Returns dict of MPLS enabled intefaces."""
        mpls_interfaces = {}
        MPLS_DEFAULTS = {
            "mpls_enabled": False,
        }

        mpls_rpc_request = "<Get><Operational><MPLS_LSD><InterfaceTable>\
        </InterfaceTable></MPLS_LSD></Operational></Get>"

        mpls_rpc_reply = ETREE.fromstring(self.device.make_rpc_call(mpls_rpc_request))

        for mpls_interface in mpls_rpc_reply.xpath(".//InterfaceTable/Interface"):
            interface = napalm.base.helpers.find_txt(
                mpls_interface, "Naming/InterfaceName"
            )

            mpls_interfaces[interface] = copy.deepcopy(MPLS_DEFAULTS)
            mpls_interfaces[interface].update(
                {
                    "mpls_enabled": True,
                }
            )
        return mpls_interfaces

    def get_isis_neighbors_xr(self):
        """Returns dict of ISIS Neighborship parameters

        Returns dict of adjacencies via rpc.
        """

        isis_neighbors = {}
        ISIS_DEFAULTS = {
            "isis_neighbor": "",
            "isis_state": False,
            "isis_nh": "",
            "isis_ipv6": False,
            "isis_metric": "",
        }

        isis_rpc_request = "<Get><Operational><ISIS><InstanceTable><Instance><Naming>\
        <InstanceName>2152</InstanceName></Naming><HostnameTable></HostnameTable>\
        <NeighborTable></NeighborTable><InterfaceTable></InterfaceTable></Instance>\
        </InstanceTable></ISIS></Operational></Get>"

        isis_rpc_reply = ETREE.fromstring(self.device.make_rpc_call(isis_rpc_request))

        for neighbor in isis_rpc_reply.xpath(".//NeighborTable/Neighbor"):
            systemID = napalm.base.helpers.find_txt(neighbor, "Naming/SystemID")
            interface = napalm.base.helpers.find_txt(neighbor, "Naming/InterfaceName")
            is_up = (
                napalm.base.helpers.find_txt(neighbor, "NeighborState")
                == "ISIS_ADJ_UP_STATE"
            )
            ipv4 = napalm.base.helpers.find_txt(
                neighbor,
                "NeighborPerAddressFamilyData/Entry/IPV4/InterfaceAddresses/Entry",
            )

            ipv6_top = False
            if napalm.base.helpers.find_txt(
                neighbor, "NeighborPerAddressFamilyData/Entry/IPV6/NextHop"
            ):
                ipv6_top = True

            # Hostname not in NeighborTable, match against SystemID from above
            for hostname in isis_rpc_reply.xpath(".//HostnameTable/Hostname"):
                host_systemID = napalm.base.helpers.find_txt(
                    hostname, "Naming/SystemID"
                )
                if host_systemID == systemID:
                    host = napalm.base.helpers.find_txt(hostname, "HostName")

            isis_neighbors[interface] = copy.deepcopy(ISIS_DEFAULTS)
            isis_neighbors[interface].update(
                {
                    "isis_neighbor": host,
                    "isis_state": is_up,
                    "isis_nh": ipv4,
                    "isis_ipv6": ipv6_top,
                }
            )

        # metric is stored in a third table
        for iface_table_interfaces in isis_rpc_reply.xpath(
            ".//InterfaceTable/Interface"
        ):
            iface_table_interface = napalm.base.helpers.find_txt(
                iface_table_interfaces, "Naming/InterfaceName"
            )
            metric = napalm.base.helpers.find_txt(
                iface_table_interfaces,
                "InterfaceStatusAndData/Enabled/PerTopologyData/Entry/Status/Enabled/Level2Metric",
            )

            try:
                isis_neighbors[iface_table_interface].update({"isis_metric": metric})
            except KeyError:  # Loopback 0 has metric, not needed
                continue
        return isis_neighbors

    def get_arp_table_xr(self):
        """Return dict of arp table by interface

        Filters interface ARP entries via rpc.
        """

        rpc_request = "<Get><Operational><ARP></ARP></Operational></Get>"
        rpc_reply = ETREE.fromstring(self.device.make_rpc_call(rpc_request))

        arp_table = {}
        ARP_DEFAULTS = {
            "arp_nh": "",
            "arp_nh_mac": "",
        }

        for entry in rpc_reply.xpath(".//EntryTable/Entry"):
            if napalm.base.helpers.find_txt(entry, "State") == "StateDynamic":
                interface = napalm.base.helpers.find_txt(entry, "Naming/InterfaceName")
                next_hop = napalm.base.helpers.find_txt(entry, "Naming/Address")

                # convert to EUI format to match ip_interface
                mac = str(
                    EUI(napalm.base.helpers.find_txt(entry, "HardwareAddress"))
                ).replace("-", ":")

            arp_table[interface] = copy.deepcopy(ARP_DEFAULTS)
            arp_table[interface].update(
                {
                    "arp_nh": next_hop,
                    "arp_nh_mac": str(mac),
                }
            )
        return arp_table

    def get_ipv6_nd_xr(self):
        """Return IPv6 Neighbors

        Uses CLI output due to poor RPC support
        """

        def parse_template_output():
            # Fix formatting of Interfaces to match the NAPALM
            # 'get_interfaces()' driver output

            for neighbor in self.parsed_output:
                short_port = neighbor[2]
                if short_port.startswith("Te"):
                    port = "TenGigE"
                elif short_port.startswith("Hu"):
                    port = "HundredGigE"
                elif short_port.startswith("Gi"):
                    port = "GigabitEthernet"
                elif short_port.startswith("BE"):
                    port = "Bundle-Ether"
                port = port + short_port[2:]

                self.nd_table[port] = copy.deepcopy(self.ND_DEFAULTS)
                self.nd_table[port].update(
                    {
                        "nd_nh": neighbor[0],
                        "nd_mac": neighbor[1],
                    }
                )

        self.nd_table = {}
        self.ND_DEFAULTS = {
            "nd_nh": "",
            "nd_mac": "",
        }

        command = 'show ipv6 neighbors | ex "fe80|Mcast"'
        output = self.cli([command])[command]

        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "w") as f:
            f.write(textfsm_nd)

        with open(tmp.name, "r") as f:
            try:
                self.parsed_output = textfsm.TextFSM(f).ParseText(output)
                parse_template_output()
                return self.nd_table

            except textfsm.parser.TextFSMTemplateError:
                print("\nNo IPv6 Neighbors for this device.\n")

    def get_optics_inventory_xr(self):
        """Return dict of optics inventory by interface

        Runs CLI command and filters with TextFSM using tempfile
        due to no RPC support.
        """

        optics = {}
        OPTICS_DEFAULTS = {
            "optic": "",
            "optic_serial": "",
        }

        command = r'show inventory | util egrep -A1 "[0-9]{1,3}\/[0-9]{1}\/(([0-9]{1})|(CPU)[0-9]{1})\/[0-9]{1,2}"'
        output = self.cli([command])[command]

        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "w") as f:
            f.write(textfsm_optics)

        with open(tmp.name, "r") as f:
            parsed_output = textfsm.TextFSM(f).ParseText(output)

        for optic_list in parsed_output:
            if "nVFabric" in optic_list[0]:
                continue

            port = re.sub("(CPU)|(module mau)", "", optic_list[0]).strip()
            optics[port] = copy.deepcopy(OPTICS_DEFAULTS)
            optics[port].update(
                {
                    "optic": optic_list[1],
                    "optic_serial": optic_list[2],
                }
            )
        return optics
