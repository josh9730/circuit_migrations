from napalm.base.exceptions import ConnectionException
import time
import json

from utils.logins import Login


#
# IOS-XR
#


class IOSXRMain:
    """Getter for IOS-XR devices (ASR-9010)"""

    def __init__(self, data):
        self.hostname = data["hostname"]
        self.device_type = data["device_type"]
        logins = Login()

        # retry login once if MFA fails
        # for i in range(2):
        #     try:
        self.napalm_connection = logins.napalm_connect(self.hostname, self.device_type)
        self.napalm_connection.open()
        # except ConnectionException:
        #     print("\n\nWaiting ~30 seconds for OTP to reset\n")
        #     continue

        # self.napalm_connection = logins.napalm_connect_test()
        # self.napalm_connection.open()

        alive = self.napalm_connection.is_alive()
        if not alive:
            raise ConnectionException(
                "\n\nConnection not established, wait 30s and re-try.\n"
            )

    def get_migration_data_full(self):
        """Return outputs for Device-wide planning.

        Typically for planning router refreshes
        """

        # with open("outputs/ip_int.json", "w") as f:
        #     ip_interfaces = self.napalm_connection.get_interfaces_ip()
        #     json.dump(ip_interfaces, f, indent=2)

        # with open("outputs/int.json", "w") as f:
        #     interaces = self.napalm_connection.get_interfaces()
        #     json.dump(interaces, f, indent=2)

        # with open("outputs/bgp.json", "w") as f:
        #     bgp = self.napalm_connection.get_bgp_neighbors()
        #     json.dump(bgp, f, indent=2)

        # with open("outputs/optics.json", "w") as f:
        #     optics = self.napalm_connection.get_optics_inventory()
        #     json.dump(optics, f, indent=2)

        # with open("outputs/isis.json", "w") as f:
        #     isis = self.napalm_connection.get_isis_neighbors()
        #     json.dump(isis, f, indent=2)

        # with open("outputs/macs.json", "w") as f:
        #     macs = self.napalm_connection.get_mac_address_table()
        #     json.dump(macs, f, indent=2)

        # with open("outputs/arp.json", "w") as f:
        #     arp = self.napalm_connection.get_arp_table()
        #     json.dump(arp, f, indent=2)

        interfaces = self.napalm_connection.get_interfaces()
        ip_interfaces = self.napalm_connection.get_interfaces_ip()
        optics = self.napalm_connection.get_optics_inventory()
        isis = self.napalm_connection.get_isis_neighbors()
        arp = self.napalm_connection.get_arp_table()
        nd = self.napalm_connection.get_ipv6_nd()
        bgp = self.napalm_connection.get_bgp_neighbors()

        # remove un-needed key
        [interfaces[i].pop("last_flapped", None) for i in interfaces.keys()]

        # collapse dicts onto interfaces
        for i in [ip_interfaces, optics, isis, arp, nd]:
            {interfaces[k].update(v) for (k, v) in i.items() if interfaces.get(k)}


        with open("outputs/comb_dict.json", "w") as f:
            json.dump(interfaces, f, indent=2)

        self.napalm_connection.close()


class MigrationInfoXR(IOSXRMain):
    """ """

    def get_interfaces(self):
        # ip_interfaces = self.napalm_connection.get_interfaces_ip()
        # interaces = self.napalm_connection.get_interfaces()
        # bgp = self.napalm_connection.get_bgp_neighbors()
        from pprint import pprint

        # pprint(bgp)
        print(self.napalm_connection.get_my_custom_method())

        self.napalm_connection.close()


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
