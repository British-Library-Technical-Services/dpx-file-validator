import logging
import os
import glob
import tkinter as tk
from tkinter import filedialog
import sys
from datetime import datetime
from tqdm import tqdm

import logging_config
import data.billboard_text as billboard_text
from inventory_generator import InventoryGenerator
from validators.dpx_sequence_validator import SequenceValidator
from validators.checksum_validator import ChecksumValidator
from validators.file_attributes_validator import FileValidator
from report_generator import ReportGenerator

file_attributes_failed = []
checksums_verified = []
checksums_failed = []


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
    location = set_source_location()
    logging_config.setup_logger(location)
    logger = logging.getLogger(__name__)

    return start_time, location, logger


def inventory_validation(location, file):
    inventory_generator = InventoryGenerator(location, file)
    inventory_generator.parse_file_name_and_type()
    inventory_generator.read_json_inventory()
    inventory_generator.parse_object_keys()
    inventory_generator.verify_file_type()
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


def mag_validation_service(file):
    format_verified = file_attributes_validation(file)

    if not format_verified:
        file_attributes_failed.append(file)

    checksum_file = f"{file}.md5"
    if os.path.exists(checksum_file):
        hash_verified = checksum_validation(file, checksum_file)

        if hash_verified:
            checksums_verified.append(file)
        else:
            checksums_failed.append(file)


def dpx_validation_service(file, checksum_manifest):
    format_verified = file_attributes_validation(file)

    if not format_verified:
        file_attributes_failed.append(file)

    hash_verified = checksum_validation(file, checksum_manifest)

    if hash_verified:
        checksums_verified.append(file)
    else:
        checksums_failed.append(file)


def dpx_sequence_check(file_list, hash_manifest):
    sequence_validator = SequenceValidator(file_list, hash_manifest)
    sequence_validator.count_manifest_lines()
    sequence_validator.count_file_sequence()

    return sequence_validator


def generate_report(
    location,
    start_time,
    end_time,
    duration,
    file_list,
    line_count,
    missing_sequence,
    files_failed,
    checksums_verified,
    checksums_failed,
):

    report = ReportGenerator(
        location,
        start_time,
        end_time,
        duration,
        file_list,
        line_count,
        missing_sequence,
        files_failed,
        checksums_verified,
        checksums_failed,
    )

    report.line_count_file_summary()
    report.missing_sequence_summary()
    report.file_attributes_summary()
    report.checksum_summary()
    report.generate_report()
    report.write_report()


def main():
    mag = "*.wav"
    film = "*.dpx"

    start_time, location, logger = intialise_service()

    logger.info(f"Location: {location}")
    logger.info(f"Start time: {start_time}")

    billboard_text.start_service_message()

    for dirpath, _, _ in os.walk(location):
        mag_files = glob.glob(os.path.join(dirpath, mag))
        film_files = glob.glob(os.path.join(dirpath, film))

        if mag_files == []:
            pass
        else:
            billboard_text.mag_file_progress()
            for file in tqdm(mag_files):
                inventory_validation(location, file)
                mag_validation_service(file)

        if film_files == []:
            pass
        else:
            billboard_text.film_file_progress()
            checksum_manifest = glob.glob(os.path.join(dirpath, "*.md5"))
            sequence_validation = dpx_sequence_check(film_files, checksum_manifest[0])
            for file in tqdm(film_files):
                inventory_validation(location, file)
                dpx_validation_service(file, checksum_manifest[0])

    end_time = datetime.now()
    # duration = end_time - start_time

    # generate_report(location,
    #     start_time,
    #     end_time,
    #     duration,
    #     file_list,
    #     sequence_validator.line_count,
    #     sequence_validator.missing_sequence,
    #     files_failed,
    #     checksums_verified,
    #     checksums_failed,
    # )

    logger.info(f"End time: {end_time}")


if __name__ == "__main__":
    main()
    input("Press any key to exit")
