"""Inventory generation utilities for DPX / mag validation workflow.

This module defines the `InventoryGenerator` class used during the initial
inventory pass of the validation service. It loads a JSON inventory structure
whose schema (top‑level key: "inventory") contains a list of per‑object
records (dictionaries). Each record tracks:

    shelfmark: Identifier used to correlate files to inventory entries.
    found: Boolean flag set to True when a matching file is seen.
    format: Expected format token (e.g. "film" or "mag").
    directory: Filesystem path where the matching asset was found.
    size: Aggregate byte size of all matching files encountered.
    count: Number of files contributing to the aggregate size.

The generator walks a supplied list of files and updates the JSON structure in place:
    1. Determine the shelfmark & type from the filename.
    2. Mark the matching inventory entry as found and record its directory.
    3. Accumulate size and increment count.
    4. Confirm that the file type matches the expected format.
    5. Persist the modifications back to the JSON file.
"""

from dotenv import load_dotenv
import logging
import sys
import glob
import os
import json

import config

logger = logging.getLogger(__name__)


class InventoryGenerator:
    """Encapsulate per‑file updates to a JSON inventory.

    Attributes are populated during instantiation and subsequent parsing
    methods; many represent key names inside each inventory record (shelfmark,
    found, format, directory, size, count)

    Args:
        location (str): Root directory being processed.
        file (str): Path to the current file whose metadata will update the inventory.
    """
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
        """Derive filename (shelfmark) and media type from path.

        For DPX files: strips extension and last 8 characters (frame number) to
        obtain the base identifier and sets type to "film". For WAV files: uses
        the full stem and sets type to "mag".
        """
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
        """Load the inventory JSON data into memory.

        Exits the process if the JSON file specified by the JSON_FILE env var
        cannot be found.
        """
        try:
            with open(self.json_data, "r") as rf:
                self.object_list = json.load(rf)

        except FileNotFoundError as e:
            print("JSON inventory file not found. SYSTEM EXIT.", {e})
            logger.critical("JSON inventory file not found. SYSTEM EXIT.", {e})
            sys.exit(1)

    def parse_object_keys(self):
        """Iterate inventory entries mapping expected semantic keys.

        Each inventory record's keys are enumerated positionally assigning
        them to semantic attribute names (shelfmark, found, format, etc.). When
        a record indicates a matching shelfmark and hasn't yet been marked
        found, size/count aggregation and format validation are performed.
        """
        try:
            for self.object in self.object_list["inventory"]:
                key_list = list(self.object.keys())
                self.shelfmark = key_list[0]
                self.found = key_list[1]
                self.format = key_list[2]
                self.directory = key_list[3]
                self.size = key_list[4]
                self.count = key_list[5]

                self.verify_shelfmark_found()
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
        """Mark inventory entry as found if filename matches shelfmark.

        Also records the directory path where the file was located.
        """
        try:
            if (
                self.filename == self.object[self.shelfmark]
                and self.object[self.found] == False
            ):
                self.object[self.found] = True
                self.object[self.directory] = self.dirpath
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
        """Accumulate total byte size and increment file count for shelfmark."""
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
        """Set format flag to True when the file type matches expected format."""
        try:
            if self.format == self.type:
                self.object[self.format] = True
            else:
                # self.object[self.format] = False
                pass

        except AttributeError as ae:
            logger.error(
                "Attribute error occurred during file object validation.", {ae}
            )
        except Exception as e:
            logger.error(
                "Unexpected error occurred during file object validation.", {e}
            )

    def write_inventory_data(self):
        """Persist the updated inventory structure back to the JSON file."""
        try:
            with open(self.json_data, "w") as wf:
                json.dump(self.object_list, wf, indent=4)

        except IOError as e:
            logger.error("Failed to write inventory data to JSON file.", {e})
