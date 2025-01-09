import os

import pandas as pd
import psycopg2
from loguru import logger
from tenacity import retry, stop_after_delay, wait_fixed


class DatabaseExtractor:
    def __init__(
        self,
        db_host: str,
        db_port: int,
        db_name: str,
        db_user: str,
        db_password: str,
        output_folder: str = None,
        queries: dict = None,
    ):
        """
        Initializes the DatabaseExtractor with database connection parameters and the folder to save CSV files.

        :param db_host: Host address of the database.
        :param db_port: Port number for the database connection.
        :param db_name: Name of the database.
        :param db_user: Username for the database.
        :param db_password: Password for the database.
        :param output_folder: Folder where CSV files will be saved. Default is None (no CSV saving).
        :param queries: A dictionary of SQL queries. Defaults to fetching all rows from the tables.
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.output_folder = output_folder
        self.queries = queries or {
            "chat_messages": "SELECT * FROM test.chat_messages;",
            "managers": "SELECT * FROM test.managers;",
            "rops": "SELECT * FROM test.rops;",
        }

    def connect_to_db(self) -> psycopg2.extensions.connection:
        """
        Establishes a connection to the database.

        :return: Database connection object.
        """
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            logger.info("Database connection established.")
            return conn
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            raise

    @retry(stop=stop_after_delay(60), wait=wait_fixed(5))
    def extract_and_save_data(self, save_to_csv: bool = False) -> dict:
        """
        Extracts data from the database using predefined or custom SQL queries and optionally saves them as CSV files.

        :param save_to_csv: If True, saves the extracted data to CSV files.
        :return: A dictionary where keys are table names and values are the corresponding DataFrames.
        """
        data_frames = {}

        try:
            conn = self.connect_to_db()

            for table_name, query in self.queries.items():
                try:
                    df = pd.read_sql_query(query, conn)
                    data_frames[table_name] = df
                    logger.info(f"Data extracted from table: {table_name}")

                    if save_to_csv and self.output_folder:
                        output_path = os.path.join(
                            self.output_folder, f"{table_name}.csv"
                        )
                        df.to_csv(output_path, index=False, encoding="utf-8")
                        logger.info(
                            f"Data from table {table_name} saved to {output_path}"
                        )
                except Exception as e:
                    logger.error(f"Error processing table {table_name}: {e}")

        except Exception as e:
            logger.error(f"Error during data extraction: {e}")
            raise

        finally:
            if "conn" in locals() and conn:
                conn.close()
                logger.info("Database connection closed.")

        return data_frames
