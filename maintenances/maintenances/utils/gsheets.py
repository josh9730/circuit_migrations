import pygsheets
import pandas as pd


class GSheets:
    """Google Sheets helpers, using pygsheets and pandas."""

    def __init__(self, data):
        """Initialize pygsheets."""
        client = pygsheets.authorize()

        try:
            self.sht = client.open(data["sheet_title"])

        except pygsheets.SpreadsheetNotFound:
            print(f"\nSheet not found, creating sheet titled: {data['sheet_title']}")
            self.sht = client.create(data["sheet_title"], folder=data["folder_id"])

    def dump_circuits_all(self, iface_dict, bgp_dict, clear=True):
        try:
            circuits_sheet = self.sht.worksheet_by_title("circuits")
            bgp_sheet = self.sht.worksheet_by_title("bgp")

        except pygsheets.exceptions.WorksheetNotFound:
            # will error if one of above exists
            circuits_sheet = self.sht.add_worksheet("circuits")
            bgp_sheet = self.sht.add_worksheet("bgp")
            self.sht.del_worksheet(self.sht.worksheet_by_title("Sheet1"))

        df = pd.DataFrame.from_dict(iface_dict, orient="index")
        df["interfaces"] = df.index
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
                "isis_ipv6",
                "arp_nh",
                "arp_nh_mac",
                "nd_nh",
                "nd_mac",
                "local_as",
                "remote_as",
                "remote_id",
                "ipv4_rx_prefixes",
                "ipv4_acpt_prefixes",
                "ipv4_tx_prefixes",
                "ipv4_bgp_uptime",
                "ipv6_rx_prefixes",
                "ipv6_acpt_prefixes",
                "ipv6_tx_prefixes",
                "ipv6_bgp_uptime",
            ]
        ]
        circuits_sheet.clear() if clear else None
        circuits_sheet.set_dataframe(df, start=(1, 1), extend=True, nan="")

        # flatten bgp_dict and create DF
        for k, v in bgp_dict.items():
            if v["address_family"].get("ipv4"):
                path = v["address_family"]["ipv4"]
            else:
                path = v["address_family"]["ipv6"]

            bgp_dict[k].update(
                {
                    "received_prefixes": path["received_prefixes"],
                    "accepted_prefixes": path["accepted_prefixes"],
                    "sent_prefixes": path["sent_prefixes"],
                }
            )
            bgp_dict[k].pop("address_family")

        df2 = pd.DataFrame.from_dict(bgp_dict, orient="index")
        df2 = df2[
            [
                "remote_id",
                "description",
                "is_enabled",
                "is_up",
                "local_as",
                "remote_as",
                "uptime",
                "received_prefixes",
                "accepted_prefixes",
                "sent_prefixes",
            ]
        ]
        bgp_sheet.clear() if clear else None
        bgp_sheet.set_dataframe(df2, start=(1, 1), extend=True, nan="")
