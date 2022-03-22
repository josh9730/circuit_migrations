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

    def get_isis_neighbors(self):
        """Returns dict of ISIS Neighborship parameters

        Returns dict of adjacencies via rpc.
        """

        isis_neighbors = {}
        ISIS_DEFAULTS = {
            "IS-IS Neighbor": "",
            "IS-IS State": False,
            "IS-IS NH": "",
            "IS-IS IPv6": False,
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
                    "IS-IS Neighbor": host,
                    "IS-IS State": is_up,
                    "IS-IS NH": ipv4,
                    "IS-IS IPv6": ipv6_top,
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
            "ARP NH": "",
            "ARP NH MAC": "",
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
                    "ARP NH": next_hop,
                    "ARP NH MAC": str(mac),
                }
            )
        return arp_table

    def get_ipv6_nd(self):
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
                        "ND NH": neighbor[0],
                        "ND MAC": neighbor[1],
                    }
                )

        self.nd_table = {}
        self.ND_DEFAULTS = {
            "ND NH": "",
            "ND MAC": "",
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

    def get_optics_inventory(self):
        """Return dict of optics inventory by interface

        Runs CLI command and filters with TextFSM using tempfile
        due to no RPC support.
        """

        optics = {}
        OPTICS_DEFAULTS = {
            "Optic": "",
            "Optic Serial": "",
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
                    "Optic": optic_list[1],
                    "Optic Serial": optic_list[2],
                }
            )
        return optics
