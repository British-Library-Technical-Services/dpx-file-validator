from dotenv import load_dotenv
import logging
import sys
import glob
import os
import json

import config

logger = logging.getLogger(__name__)


class InventoryGenerator:
    def __init__(self, location, file):
        load_dotenv()

        self.json_data = os.getenv("JSON_FILE")
        self.location = location
        self.file = file
        self.file_list = glob.glob(location + "/**/*.*", recursive=True)
        self.object_list = []
        self.object = {}
        self.shelfmark = None
        self.found = None
        self.format = None
        self.directory = None
        self.size = None
        self.count = None
        self.filename = None
        self.type = None
        self.dirpath = None
        self.shelmark_data_size = 0

    def parse_file_name_and_type(self):
        try:
            self.dirpath = os.path.dirname(self.file)
            if self.file.endswith(".dpx"):
                self.filename = os.path.basename(self.file.split(".")[0][:-8])
                self.type = "film"

            elif self.file.endswith(".wav"):
                self.filename = os.path.basename(self.file.split(".")[0])
                self.type = "mag"

        except AttributeError as ae:
            logger.error("Attribute error occurred while parsing file data.", {ae})
        except Exception as e:
            logger.error("Error occurred while parsing file data.", {e})

    def read_json_inventory(self):
        try:
            with open(self.json_data, "r") as rf:
                self.object_list = json.load(rf)

        except FileNotFoundError as e:
            print("JSON inventory file not found. SYSTEM EXIT.", {e})
            logger.critical("JSON inventory file not found. SYSTEM EXIT.", {e})
            sys.exit(1)

    def parse_object_keys(self):
        try:
            for self.object in self.object_list["inventory"]:
                key_list = list(self.object.keys())
                self.shelfmark = key_list[0]
                self.found = key_list[1]
                self.format = key_list[2]
                self.directory = key_list[3]
                self.size = key_list[4]
                self.count = key_list[5]

                self.verify_shelfmark_found
                if self.object[self.found]:
                    self.get_size_and_count()
                    self.verify_file_type()
                else:
                    pass

        except KeyError as ke:
            logger.error("Key error occurred while parsing object keys.", {ke})
        except Exception as e:
            logger.error("Error occurred while parsing object keys.", {e})

    def verify_shelfmark_found(self):
        try:
            if (
                self.filename == self.object[self.shelfmark]
                and self.object[self.found] == False
            ):
                self.object[self.found] = True
                self.object[self.directory] = self.dirpath

                self.verify_file_type()

            else:
                pass

        except AttributeError as ae:
            logger.error(
                "Attribute error occurred during shelfmark verification.", {ae}
            )
        except Exception as e:
            logger.error(
                "Unexpected error occurred during shelfmark verification.", {e}
            )

    def get_size_and_count(self):
        try:
            if self.filename == self.object[self.shelfmark]:
                self.shelmark_data_size = (
                    os.path.getsize(self.file) + self.object[self.size]
                )
                self.object[self.size] = self.shelmark_data_size
                self.object[self.count] += 1
            else:
                pass
        except AttributeError as ae:
            logger.error(
                "Attribute error occurred during size and count retrieval.", {ae}
            )
        except Exception as e:
            logger.error(
                "Unexpected error occurred during size and count retrieval.", {e}
            )

    def verify_file_type(self):
        try:
            if self.format == self.type:
                self.object[self.format] = True
            else:
                self.object[self.format] = False

        except AttributeError as ae:
            logger.error(
                "Attribute error occurred during file object validation.", {ae}
            )
        except Exception as e:
            logger.error(
                "Unexpected error occurred during file object validation.", {e}
            )

    def write_inventory_data(self):
        try:
            with open(self.json_data, "w") as wf:
                json.dump(self.object_list, wf, indent=4)

        except IOError as e:
            logger.error("Failed to write inventory data to JSON file.", {e})
