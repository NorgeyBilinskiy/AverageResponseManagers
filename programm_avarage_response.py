import warnings
from datetime import timedelta

from loguru import logger

from src import Config
from src import ChatResponseAnalyzer
from src import DatabaseExtractor
from src import GoogleSheetsHandler


def main():
    logger.info("START SCRIPT")

    # === Load Configuration ===
    WORK_START = timedelta(hours=9, minutes=30, seconds=0)
    WORK_END = timedelta(hours=23, minutes=59, seconds=59, microseconds=59)
    UTC_OFFSET = timedelta(hours=3)

    config = Config()

    DB_HOST = config.bd_info().get("HOST")
    DB_PORT = config.bd_info().get("PORT")
    DB_NAME = config.bd_info().get("NAME")
    DB_USER = config.bd_info().get("USER")
    DB_PASSWORD = config.bd_info().get("PASSWORD")

    PATH_GOOGLE_TOKEN = config.get_paths().get("google_token")
    SPREADSHEET_ID = config.get_google_sheets_info().get("SPREADSHEET_ID")
    RANGE_NAME = config.get_google_sheets_info().get("RANGE_NAME")

    # === Suppress Warnings ===
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        message="pandas only supports SQLAlchemy connectable",
    )

    # === Extract Data from Database ===
    db_extractor = DatabaseExtractor(
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_name=DB_NAME,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
    )

    dict_table = db_extractor.extract_and_save_data(save_to_csv=True)

    if dict_table:
        logger.info("Data extraction completed successfully.")
    else:
        logger.error("No data was extracted.")

    df_chat_messages = dict_table["chat_messages"]
    df_managers = dict_table["managers"]
    df_rops = dict_table["rops"]

    # === Analyze Chat Messages ===
    analyzer = ChatResponseAnalyzer(
        work_start=WORK_START,
        work_end=WORK_END,
        utc_offset=UTC_OFFSET,
    )

    average_response_time_pandas = analyzer.analyze_result(
        df_chat_messages, df_managers, df_rops
    )

    # === Save Data to Google Sheets ===
    gs_handler = GoogleSheetsHandler(SPREADSHEET_ID, PATH_GOOGLE_TOKEN)
    gs_handler.save_data_table(RANGE_NAME, average_response_time_pandas)

    logger.info("END SCRIPT")


if __name__ == "__main__":
    main()
