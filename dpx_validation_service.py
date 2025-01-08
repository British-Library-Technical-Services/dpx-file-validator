import logging
import glob
import tkinter as tk
from tkinter import filedialog
import sys
from datetime import datetime
from tqdm import tqdm

import logging_config
import service_billboard
from sequence_validator import SequenceValidator
from hash_validator import ChecksumValidator
from file_validator import FileValidator
from report_generator import ReportGenerator

def capture_file_list():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        location = filedialog.askdirectory()
        if location != "":
            try: 
                file_list = sorted(glob.glob(location + "/*.dpx"))
                hash_manifest = glob.glob(location + "/*.md5")

                return location, file_list, hash_manifest
            
            except Exception as e:
                logging.error("glob pattern did not match", e)
        else:
            logging.error("No source location selected.  Service will exit")
            sys.exit()

    except Exception as e:
        logging.error("Unable able to open directory", e)

def intialise_service():
    start_time = datetime.now()
    location, file_list, hash_manifest = capture_file_list()
    logging_config.setup_logger(location)
    logger = logging.getLogger(__name__)
    
    return start_time, location, file_list, hash_manifest, logger

def dpx_sequence_check(file_list, hash_manifest):
    sequence_validator = SequenceValidator(file_list, hash_manifest)
    sequence_validator.count_manifest_lines()
    sequence_validator.count_file_sequence()

    return sequence_validator

def validate_checksums_files(file, hash_manifest):
    checksums_verified = []
    checksums_failed = []
    files_failed = []

    checksum_validator = ChecksumValidator(file, hash_manifest[0])

    checksum_validator.file_name_extract()
    checksum_validator.seek_in_manifest()

    
    if checksum_validator.file_found:
        
        checksum_validator.generate_file_hash()
        checksum_validator.validate_checksum()

        if checksum_validator.hash_verified:
            checksums_verified.append(file)

            file_validator = FileValidator(file)
            file_validator.read_attributes()
            file_validator.parse_attributes()
            file_validator.validate_attributes()
            
            if not file_validator.format_verified:
                files_failed.append(file)
        else:
            checksums_failed.append(file)

    return checksums_verified, checksums_failed, files_failed

def generate_report(location,
        start_time,
        end_time,
        duration,
        file_list,
        line_count,
        missing_sequence,
        files_failed,
        checksums_verified,
        checksums_failed):
    
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
    start_time, location, file_list, hash_manifest, logger = intialise_service()

    logger.info(f"Location: {location}")
    logger.info(f"Start time: {start_time}")

    sequence_validator = dpx_sequence_check(file_list, hash_manifest[0])

    service_billboard.start_service_message()

    for file in tqdm(file_list):
        try:
            checksums_verified, checksums_failed, files_failed = validate_checksums_files(file, hash_manifest[0])
        except Exception as e:
            logger.error(f"{file}, {e}")

    end_time = datetime.now()
    duration = end_time - start_time

    generate_report(location,
        start_time,
        end_time,
        duration,
        file_list,
        sequence_validator.line_count,
        sequence_validator.missing_sequence,
        files_failed,
        checksums_verified,
        checksums_failed,
    )

    logger.info(f"End time: {end_time}")

if __name__ == "__main__":
    main()
    input("Press any key to exit")