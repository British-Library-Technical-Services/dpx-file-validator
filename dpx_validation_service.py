import logging
import glob
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from tqdm import tqdm

import logging_config

from sequence_validator import SequenceValidator
from hash_validator import ChecksumValidator
from file_validator import FileValidator
from report_generator import ReportGenerator

def main():
    files_failed = []
    checksums_verified = []
    checksums_failed = []

    start_time = datetime.now()

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    location = filedialog.askdirectory()

    logging_config.setup_logger(location)
    logger = logging.getLogger(__name__)

    logger.info(f"Location: {location}")
    logger.info(f"Start time: {start_time}")

    file_list = sorted(glob.glob(location + "/*.dpx"))
    hash_manifest = glob.glob(location + "/*.md5")

    sequence_validator = SequenceValidator(file_list, hash_manifest[0])
    sequence_validator.count_manifest_lines()
    sequence_validator.count_file_sequence()

    for file in tqdm(file_list):
        try:
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
        except Exception as e:
            logger.error(f"{file}, {e}")

    end_time = datetime.now()
    duration = end_time - start_time

    report = ReportGenerator(
        location,
        start_time,
        end_time,
        duration,
        len(file_list),
        sequence_validator.line_count,
        sequence_validator.missing_sequence,
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

    logger.info(f"End time: {end_time}")

if __name__ == "__main__":
    main()