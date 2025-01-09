import os

from loguru import logger

from .utils import FileValidator, FileHandler


class Config:
    def __init__(self):
        # === Path Configurations ===
        self.BASE_DIR = os.getcwd()
        self.PATH_TO_VALIDATE = {
            "google_token": os.path.join(
                self.BASE_DIR, "./settings/google_api", "token.json"
            ),
            "google_sheets_info": os.path.join(
                self.BASE_DIR, "./settings/google_api", "google_sheets_info.yaml"
            ),
            "db_info": os.path.join(
                self.BASE_DIR, "./settings/db_api", "connect.yaml"
            ),
        }

        # === Path Validation ===
        logger.info("Start checking for validity of paths to configuration files.")
        for name, path in self.PATH_TO_VALIDATE.items():
            FileValidator.validate_file_path(path)
        logger.info("All file paths have been validated successfully.")


        # === Google Sheets Configuration ===
        google_sheets_info = FileHandler.load_yaml(
            self.PATH_TO_VALIDATE["google_sheets_info"]
        )
        self.SPREADSHEET_ID = google_sheets_info["SPREADSHEET_ID"]
        self.RANGE_NAME = google_sheets_info["RANGE_NAME"]

        # === DB Configuration ===
        db_info = FileHandler.load_yaml(
            self.PATH_TO_VALIDATE["db_info"]
        )
        self.HOST = db_info["database"]["host"]
        self.PORT = db_info["database"]["port"]
        self.NAME = db_info["database"]["name"]
        self.USER = db_info["database"]["user"]
        self.PASSWORD = db_info["database"]["password"]

    def bd_info(self):
        return {
            "HOST": self.HOST,
            "PORT": self.PORT,
            "NAME": self.NAME,
            "USER": self.USER,
            "PASSWORD": self.PASSWORD,
        }

    def get_google_sheets_info(self):
        return {
            "SPREADSHEET_ID": self.SPREADSHEET_ID,
            "RANGE_NAME": self.RANGE_NAME,
        }

    def get_paths(self):
        return self.PATH_TO_VALIDATE
