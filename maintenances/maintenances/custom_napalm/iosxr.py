from napalm.iosxr.iosxr import IOSXRDriver
import napalm.base.helpers
import copy
import textfsm
import tempfile
import re
from lxml import etree as ETREE
from netaddr import EUI

from . import textfsm_optics


class CustomIOSXRDriver(IOSXRDriver):
    """Extends base IOSXRDriver for custom methods"""

    def get_isis_neighbors(self):
        """Returns dict of ISIS Neighborship parameters

        Returns dict of adjacencies via rpc.
        """

        isis_neighbors = {}
        ISIS_DEFAULTS = {
            "IS-IS": {
                "Hostname": "",
                "System ID": "",
                "Up": False,
                "IPv4 NH": "",
                "IPv6 Topology": False,
            }
        }

        isis_rpc_request = "<Get><Operational><ISIS><InstanceTable><Instance><Naming>\
        <InstanceName>2152</InstanceName></Naming><HostnameTable></HostnameTable>\
        <NeighborTable></NeighborTable></Instance></InstanceTable></ISIS></Operational></Get>"

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
                    "IS-IS": {
                        "Hostname": host,
                        "System ID": systemID,
                        "Up": is_up,
                        "IPv4 NH": ipv4,
                        "IPv6 Topology": ipv6_top,
                    }
                }
            )
        return isis_neighbors

    def get_arp_table(self):
        """Return dict of arp table by interface

        Filters interface ARP entries via rpc.
        """

        rpc_request = "<Get><Operational><ARP></ARP></Operational></Get>"
        rpc_reply = ETREE.fromstring(self.device.make_rpc_call(rpc_request))

        arp_table = {}
        ARP_DEFAULTS = {
            "ARP": {
                "Next-Hop": "",
                "NH MAC": "",
            }
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
                    "ARP": {
                        "Next-Hop": next_hop,
                        "MAC": str(mac),
                    }
                }
            )
        return arp_table

    def get_ipv6_nd(self):
        """Return IPv6 Neighbor Discovery

        Returns dict of ND adjacencies via rpc.
        """
        nd_table = {}
        ND_DEFAULTS = {
            "IPv6 ND": {
                "Next-Hop": "",
                "MAC": "",
            }
        }

        rpc_request = "<Get><Operational><IPV6NodeDiscovery></IPV6NodeDiscovery></Operational></Get>"
        rpc_reply = ETREE.fromstring(self.device.make_rpc_call(rpc_request))

        for entry in rpc_reply.xpath(".//BundleInterfaceTable/BundleInterface"):
            if napalm.base.helpers.find_txt(entry, "IsInterfaceEnabled") == "true":
                interface = napalm.base.helpers.find_txt(entry, "Naming/InterfaceName")
                next_hop = napalm.base.helpers.find_txt(
                    entry, "GlobalAddressList/Entry/IPv6Address"
                )

                # convert to EUI format to match ip_interface
                mac = str(EUI(napalm.base.helpers.find_txt(entry, "macAddr")))

                nd_table[interface] = copy.deepcopy(ND_DEFAULTS)
                nd_table[interface].update(
                    {
                        "IPv6 ND": {
                            "Next-Hop": next_hop,
                            "MAC": mac,
                        }
                    }
                )
        return nd_table

    def get_optics_inventory(self):
        """Return dict of optics inventory by interface

        Runs CLI command and filters with TextFSM using tempfile.
        Filters nVFabric & CPU strings.
        """

        optics = {}
        OPTICS_DEFAULTS = {
            "Optic": {
                "PID": "",
                "Serial": "",
            }
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
                    "Optic": {
                        "PID": optic_list[1],
                        "Serial": optic_list[2],
                    }
                }
            )
        return optics
