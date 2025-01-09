from typing import Any

from googleapiclient.discovery import build
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from loguru import logger
from tenacity import retry, stop_after_delay, wait_fixed


class GoogleSheetsHandler:
    """
    A class for interacting with Google Sheets to load data into a DataFrame or retrieve a single cell's value.
    """

    def __init__(self, spreadsheet_id: str, path_google_key: str) -> None:
        """
        Initialize the GoogleSheetsHandler.

        Parameters:
        spreadsheet_id (str): Google Sheets ID.
        path_google_key (str): Path to the JSON file containing the Google API key.
        """
        self.spreadsheet_id = spreadsheet_id
        self.path_google_key = path_google_key
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    @staticmethod
    def _authenticate(path_google_key: str, scopes: list[str]) -> Any:
        """
        Authenticate with the Google Sheets API.

        Parameters:
        path_google_key (str): Path to the JSON file containing the Google API key.
        scopes (list[str]): Scopes for Google API access.

        Returns:
        Any: The authorized HTTP object for accessing Google Sheets.
        """
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            path_google_key, scopes
        )
        return credentials.authorize(httplib2.Http())

    @retry(stop=stop_after_delay(60 * 30), wait=wait_fixed(5))
    def get_data_table(self, range_name: str) -> pd.DataFrame:
        """
        Load data from Google Sheets into a DataFrame.

        Parameters:
        range_name (str): The range of cells to retrieve the data from.

        Returns:
        pd.DataFrame: Data from Google Sheets in DataFrame format.
        """
        try:
            http_auth = self._authenticate(self.path_google_key, self.scopes)
            service = build("sheets", "v4", http=http_auth)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )
            values = result.get("values", [])

            if not values:
                logger.warning("Data not found in the specified range.")
                return pd.DataFrame()

            df = pd.DataFrame(values)
            df.columns = df.iloc[0]
            df.columns = df.columns.astype(str)
            df.drop(index=df.index[0], inplace=True)
            if "ticker" in df.columns:
                df["ticker"] = df["ticker"].astype(str)
                df.set_index("ticker", inplace=True)
            elif "date" in df.columns:
                df.set_index("date", inplace=True)
                df.index = pd.to_datetime(df.index)
            logger.info("The data has been successfully downloaded from Google Sheets.")
            return df

        except Exception as e:
            logger.error(f"Error when loading data: {e}")
            raise

    @retry(stop=stop_after_delay(60 * 30), wait=wait_fixed(5))
    def get_cell_value(self, range_name: str) -> str:
        """
        Retrieve a single cell's value from Google Sheets.

        Parameters:
        range_name (str): The range of the cell to retrieve the data from.

        Returns:
        str: The value of the cell as a string.
        """
        try:
            http_auth = self._authenticate(self.path_google_key)
            service = build("sheets", "v4", http=http_auth)
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_name)
                .execute()
            )
            values = result.get("values", [])

            if not values or not values[0]:
                logger.warning("The specified cell is empty or does not exist.")
                return ""

            cell_value = values[0][0]
            logger.info(f"Successfully retrieved cell value: {cell_value}")
            return cell_value

        except Exception as e:
            logger.error(f"Error when retrieving cell value: {e}")
            raise

    @retry(stop=stop_after_delay(60 * 30), wait=wait_fixed(5))
    def save_data_table(self, range_name: str, df: pd.DataFrame) -> None:
        """
        Save data from a DataFrame to Google Sheets.

        Parameters:
        range_name (str): The range of cells to write the data to.
        df (pd.DataFrame): DataFrame to save to Google Sheets.

        Returns:
        None
        """
        try:
            http_auth = self._authenticate(self.path_google_key, self.scopes)
            service = build("sheets", "v4", http=http_auth)
            sheet = service.spreadsheets()

            df = df.where(pd.notnull(df), "")

            values = [df.columns.tolist()] + df.reset_index(drop=True).values.tolist()

            body = {"values": values}

            sheet.values().clear(
                spreadsheetId=self.spreadsheet_id, range=range_name
            ).execute()
            sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            ).execute()

            logger.info("Data has been successfully saved to Google Sheets.")

        except Exception as e:
            logger.error(f"Error when saving data: {e}")
            raise
