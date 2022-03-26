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

    def dump_circuits_all(self, interfaces_df, bgp_missing_df, clear=True):
        try:
            circuits_sheet = self.sht.worksheet_by_title("circuits")
            bgp_sheet = self.sht.worksheet_by_title("bgp")

        except pygsheets.exceptions.WorksheetNotFound:
            # will error if one of above exists
            circuits_sheet = self.sht.add_worksheet("circuits")
            bgp_sheet = self.sht.add_worksheet("bgp")
            self.sht.del_worksheet(self.sht.worksheet_by_title("Sheet1"))

        circuits_sheet.clear() if clear else None
        circuits_sheet.set_dataframe(interfaces_df, start=(1, 1), fit=True, nan="")

        bgp_sheet.clear() if clear else None
        bgp_sheet.set_dataframe(bgp_missing_df, start=(1, 1), fit=True, nan="")
