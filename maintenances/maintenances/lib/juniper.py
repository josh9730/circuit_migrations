import time
from napalm.base.exceptions import ConnectionException

from utils.logins import Login
from lib import parsers


class Main:
    def __init__(self, data):
        self.hostname = data["hostname"]
        self.data = data
        self.device_type = data["device_type"]
        self.logins = Login()

        self.start_time = time.time()
        self.napalm_connection = self.logins.napalm_connect(
            self.hostname, self.device_type
        )
        self.napalm_connection.open()

        if not self.napalm_connection.is_alive():
            raise ConnectionException(
                "\n\nConnection not established, wait 30s and re-try.\n"
            )

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
        return ifaces_all

    def get_migration_data_full(self):
        pass

    def devices_pms(self) -> dict:
        """Dumps JSON of Device-specific outputs for PMs.
        
        optics? 
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
            "Non-Port BGP": bgp,
            "MSDP": msdp,
            "PIM": pim,
            "Interfaces": interfaces_all,
        }
        return output

    def circuits_pms(self):
        pass
