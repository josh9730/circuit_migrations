import socket
import ipaddress


def xr_format_ip_int(data: dict):
    """Collapse napalm ip_interface output to:

    {
        {{ INT }}:
            ipv4_address: {{ IP }},
            ipv6_address: {{ IP }}
    }
    """
    output = {}
    for k, v in data.items():
        ip_dict = {}
        for i in range(4, 7, 2):
            ip = v.get(f"ipv{i}")
            if ip:
                address = next(iter(ip))
                ip_dict.update(
                    {f"ipv{i}_address": f"{address}/{ip[address]['prefix_length']}"}
                )

        output.update({k: ip_dict})
    return output


def xr_collapse_bgp(iface_dict, bgp_dict):
    """Collapse BGP dictionary onto the consolidated interface dictionary.

    BGP peerings matched with Interface by ARP/ND neighbors. Once a peering
    is matched with an interface, the BGP dict is popped, allowing the peerings
    not associated with an interface to be returned later.
    """
    for iface in iface_dict:
        v4_neighbor, v6_neighbor = None, None

        # iBGP
        if iface_dict[iface].get("isis_neighbor"):
            isis_neighbor = iface_dict[iface]["isis_neighbor"]
            v4_neighbor = socket.gethostbyname(isis_neighbor)
            try:
                v6_neighbor = socket.getaddrinfo(
                    isis_neighbor, None, socket.AF_INET6, socket.SOCK_DGRAM
                )[0][-1][0]
            except IndexError:
                print(f"{iface_dict} has no IPv6 Neighbor.")

        # eBGP
        elif iface_dict[iface].get("arp_nh"):
            v4_neighbor = iface_dict[iface]["arp_nh"]
            if iface_dict[iface].get("nd_nh"):
                v6_neighbor = iface_dict[iface]["nd_nh"]

        # update interface dict with BGP neighbor
        if v4_neighbor and bgp_dict.get(v4_neighbor):
            iface_dict[iface].update(bgp_dict[v4_neighbor])

            # remove matched peer, un-matched will be dumped to a second sheet
            bgp_dict.pop(v4_neighbor, None)

        if v6_neighbor and bgp_dict.get(v6_neighbor):
            iface_dict[iface].update(bgp_dict[v6_neighbor])

            # remove matched peer, un-matched will be dumped to a second sheet
            bgp_dict.pop(v6_neighbor, None)
    return iface_dict, bgp_dict


def xr_format_bgp_detail(data: dict):
    """Format BGP detail output to be keyed by peer IP.

    NAPALM BGP detail output is by default a list of ASNs.
    This is flatted to nested dict by peer IP, and removes unneeded data.
    """
    bgp_output = {}
    data = data["global"]
    for peer_list in data.values():
        for peer in peer_list:

            ip_type = "v4"
            if isinstance(
                ipaddress.ip_address(peer["remote_address"]), ipaddress.IPv6Address
            ):
                ip_type = "v6"

            dns = "No A/AAAA Record"
            try:
                local_dns = socket.gethostbyaddr(peer["local_address"])[0].split(".")[0]
            except socket.herror:
                local_dns = dns

            try:
                remote_dns = socket.gethostbyaddr(peer["remote_address"])[0].split(".")[
                    0
                ]
            except socket.herror:
                remote_dns = dns

            bgp_output.update(
                {
                    peer["remote_address"]: {
                        "local_as": peer["local_as"],
                        "remote_as": peer["remote_as"],
                        "router_id": peer["router_id"],
                        "local_address": peer["local_address"],
                        "local_dns": local_dns,
                        "remote_address": peer["remote_address"],
                        "remote_dns": remote_dns,
                        "multihop": peer["multihop"],
                        "multipath": peer["multipath"],
                        "import_policy": peer["import_policy"],
                        "export_policy": peer["export_policy"],
                        "connection_state": peer["connection_state"],
                        f"{ip_type}_received_prefix": peer["received_prefix_count"],
                        f"{ip_type}_accepted_prefix": peer["accepted_prefix_count"],
                        f"{ip_type}_advertised_prefix": peer["advertised_prefix_count"],
                    }
                }
            )
    return bgp_output


def xr_sort_df_circuits_columns(df):
    df = df[
        [
            "interfaces",
            "description",
            "speed",
            "mtu",
            "is_enabled",
            "is_up",
            "optic",
            "optic_serial",
            "mac_address",
            "ipv4_address",
            "ipv6_address",
            "isis_neighbor",
            "isis_state",
            "isis_nh",
            "isis_metric",
            "isis_ipv6",
            "mpls_enabled",
            "arp_nh",
            "arp_nh_mac",
            "nd_nh",
            "nd_mac",
            "local_as",
            "remote_as",
            "connection_state",
            "router_id",
            "local_address",
            "local_dns",
            "remote_address",
            "remote_dns",
            "multihop",
            "multipath",
            "import_policy",
            "export_policy",
            "v4_received_prefix",
            "v4_accepted_prefix",
            "v4_advertised_prefix",
            "v6_received_prefix",
            "v6_accepted_prefix",
            "v6_advertised_prefix",
        ]
    ]
    return df
