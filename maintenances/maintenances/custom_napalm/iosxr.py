from napalm.iosxr.iosxr import IOSXRDriver
import napalm.base.helpers
import copy
import textfsm
import tempfile
from lxml import etree as ETREE

from . import textfsm_optics


class CustomIOSXRDriver(IOSXRDriver):
    """Extends base IOSXRDriver for custom methods"""

    def get_isis_neigbors(self):
        """Returns dict of ISIS Neighborship parameters"""

        isis_neighbors = {}
        ISIS_DEFAULTS = {
            "Hostname": "",
            "System ID": "",
            "Up": False,
            "IPv4 NH": "",
            "IPv6 Topology": False,
        }

        isis_rpc_request = "<Get><Operational><ISIS><InstanceTable><Instance><Naming>\
        <InstanceName>2152</InstanceName></Naming><HostnameTable></HostnameTable><NeighborTable></NeighborTable></Instance></InstanceTable></ISIS></Operational></Get>"

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
                    "Hostname": host,
                    "System ID": systemID,
                    "Up": is_up,
                    "IPv4 NH": ipv4,
                    "IPv6 Topology": ipv6_top,
                }
            )
        return isis_neighbors

    def get_optics_inventory(self):
        """Return dict of optics inventory by interface

        The string portion of the interface name (i.e. 'TenGigE') is not returned.
        """

        optics = {}
        OPTICS_DEFAULTS = {
            "PID": "",
            "Serial": "",
        }

        command = r'show inventory | util egrep -A1 "[0-9]{1,3}\/[0-9]{1}\/(([0-9]{1})|(CPU)[0-9]{1})\/[0-9]{1,2}"'
        output = self.cli([command])[command]

        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "w") as f:
            f.write(textfsm_optics)

        with open(tmp.name, "r") as f:
            parsed_output = textfsm.TextFSM(f).ParseText(output)

        for i in parsed_output:
            port = i[0].replace("CPU", "")
            optics[port] = copy.deepcopy(OPTICS_DEFAULTS)
            optics[port].update(
                {
                    "PID": i[1],
                    "Serial": i[2],
                }
            )
        return optics
