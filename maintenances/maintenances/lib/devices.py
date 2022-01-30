
from napalm.base.exceptions import ConnectionException
from utils.logins import Login


#
# IOS-XR
#

class IOSXRMain:
    """Getter for IOS-XR devices (ASR-9010)"""
    def __init__(self, data):
        self.hostname = data['hostname']
        self.device_type = data['device_type']
        logins = Login()

        try:
            self.napalm_connection = logins.napalm_connect(self.hostname, self.device_type)
            self.napalm_connection.open()
        except ConnectionException:
            print("\n\nWait ~30 seconds for OTP to reset\n")

        alive = self.napalm_connection.is_alive()
        if not alive:
            raise ConnectionException('\n\nConnection not established, wait 30s and re-try.\n')

    def get_migration_data_full(self):
        """Return outputs for Device-wide planning.

        Typically for planning router refreshes
        """
        ip_interfaces = self.napalm_connection.get_interfaces_ip()
        interaces = self.napalm_connection.get_interfaces()
        bgp = self.napalm_connection.get_bgp_neighbors()
        # get optics_custom
        # get isis_c
        # get pim_c
        # get_mac_address_table	?

        self.napalm_connection.close()



class MigrationInfoXR(IOSXRMain):
    """
    """

    def get_interfaces(self):
        # ip_interfaces = self.napalm_connection.get_interfaces_ip()
        # interaces = self.napalm_connection.get_interfaces()
        # bgp = self.napalm_connection.get_bgp_neighbors()
        from pprint import pprint
        # pprint(bgp)
        print(self.napalm_connection.get_my_custom_method())

        self.napalm_connection.close()


class DeviceXR(IOSXR):
    """Device-specific methods"""

    pass


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