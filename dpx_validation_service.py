import logging
import os
from dotenv import load_dotenv
import glob
import tkinter as tk
from tkinter import filedialog
import sys
from datetime import datetime
from tqdm import tqdm

import logging_config
import data.billboard_text as billboard_text
import config

from progress_loop import Spinner
from inventory_generator import InventoryGenerator
from validators.dpx_sequence_validator import SequenceValidator
from validators.checksum_validator import ChecksumValidator
from validators.file_attributes_validator import FileValidator

cumulative_mag_files = []
cumulative_film_files = []
file_attributes_failed = []
checksums_verified = []
checksums_failed = []

def test_source_location():
    load_dotenv()
    try:
        location = os.getenv("TEST_LOCATION")
        if location != "":
            try:
                return location

            except Exception as e:
                logging.error(e)
        else:
            logging.error("No source location selected.  Service will exit")
            sys.exit()

    except Exception as e:
        logging.error("Unable able to open directory", e)


def set_source_location():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        location = filedialog.askdirectory()
        if location != "":
            try:
                return location

            except Exception as e:
                logging.error(e)
        else:
            logging.error("No source location selected.  Service will exit")
            sys.exit()

    except Exception as e:
        logging.error("Unable able to open directory", e)


def intialise_service():
    start_time = datetime.now()
    # location = test_source_location()
    location = set_source_location()
    logging_config.setup_logger()
    logger = logging.getLogger(__name__)

    return start_time, location, logger


def inventory_validation(location, file):
    inventory_generator = InventoryGenerator(location, file)
    inventory_generator.parse_file_name_and_type()
    inventory_generator.read_json_inventory()
    inventory_generator.parse_object_keys()
    inventory_generator.write_inventory_data()


def file_attributes_validation(file):
    file_validator = FileValidator(file)
    file_validator.read_attributes()
    file_validator.format_attributes_validation()

    return file_validator.format_verified


def checksum_validation(file, checksums):
    checksum_validator = ChecksumValidator(file, checksums)
    checksum_validator.generate_file_hash()
    checksum_validator.file_name_extract()
    checksum_validator.seek_in_manifest()
    checksum_validator.validate_checksum()

    return checksum_validator.hash_verified


def dpx_sequence_check(files, path):
    md5 = config.CONFIG["extensions"]["CHECKSUM"]
    checksum_manifest = glob.glob(os.path.join(path, md5))
    sequence_validator = SequenceValidator(files, checksum_manifest[0], path)
    sequence_validator.count_manifest_lines()
    sequence_validator.count_file_sequence()

    return checksum_manifest, sequence_validator


def process_file_inventory(files, path):
    for file in files:
        inventory_validation(path, file)


def process_file_validation(files):
    for file in tqdm(files, desc="MediaInfo"):
        format_verified = file_attributes_validation(file)
        if not format_verified:
            file_attributes_failed.append(file)
        

def mag_checksum_validation(files):
    checksum_format = config.CONFIG["extensions"]["HASH_FORMAT"]
    for file in tqdm(files, desc="Checksums"):
        checksum_file = f"{file}.{checksum_format}"
        
        if os.path.exists(checksum_file):
            hash_verified = checksum_validation(file, checksum_file)

            if hash_verified:
                checksums_verified.append(file)
            else:
                checksums_failed.append(file)
        else:
            logging.error(f"No checksum file for {file}")


def film_checksum_validation(files, checksum_file):
    for file in tqdm(files, desc="Checksums"):
        hash_verified = checksum_validation(file, checksum_file)

        if hash_verified:
            checksums_verified.append(file)
        else:
            checksums_failed.append(file)


def main():
    MAG = config.CONFIG["extensions"]["MAG"]
    FILM = config.CONFIG["extensions"]["FILM"]

    start_time, location, logger = intialise_service()

    logger.info(f"Location: {location}")
    logger.info(f"Start time: {start_time}")

    billboard_text.start_service_message()
    billboard_text.inventory_text(location)
    progress_spinner = Spinner()
    progress_spinner.start()

    # File Inventory Checks
    try:
        for dirpath, _, _ in os.walk(location):
            mag_files = sorted(glob.glob(os.path.join(dirpath, MAG)))
            film_files = sorted(glob.glob(os.path.join(dirpath, FILM)))

            if mag_files or film_files:
                file_inventory_list = mag_files + film_files
                process_file_inventory(files=file_inventory_list, path=dirpath)
    
    except Exception as e:
        logger.critical(f"Error processing directory: {e}")
        sys.exit(1)
    
    finally:
        progress_spinner.stop()

    # File-Checksum Validation Checks
    billboard_text.validation_text()
    
    try:
        for dirpath, _, _ in os.walk(location):
            mag_files = sorted(glob.glob(os.path.join(dirpath, MAG)))
            film_files = sorted(glob.glob(os.path.join(dirpath, FILM)))

            if mag_files:
                billboard_text.mag_files_processing_text(path=dirpath)
                cumulative_mag_files.extend(mag_files)
                process_file_validation(files=mag_files)
                mag_checksum_validation(files=mag_files)

            if film_files:
                billboard_text.dpx_files_processing_text(path=dirpath)
                cumulative_film_files.extend(film_files)
                checksums, sequence_validation = dpx_sequence_check(files=film_files, path=dirpath)
                process_file_validation(files=film_files)
                film_checksum_validation(files=film_files, checksum_file=checksums[0])
        

    except Exception as e:
        logger.critical(f"Error processinf files: {e}")
        sys.exit(1)

    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"End time: {end_time}")
    logger.info(f"Total time: {duration}")
    logger.info(f"Film scans: {len(cumulative_film_files)}")
    logger.info(f"Mag files: {len(cumulative_mag_files)}")
    logger.info(f"Failed file attributes: {len(file_attributes_failed)}")
    logger.info(f"Failed checksums: {len(checksums_failed)}")


if __name__ == "__main__":
    main()
    input("Press any key to exit")
