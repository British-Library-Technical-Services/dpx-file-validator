"""DPX File Validation Service.

This module provides the CLI / GUI (folder chooser) workflow for
validating DPX film scan sequences and accompanying magnetic (mag) audio files.
It performs two broad phases:

1. Inventory phase – walk the provided directory tree, derive inventory
   metadata for recognised file types, and write results out through the
   `InventoryGenerator` helper.
2. Validation phase – for each discovered file it validates:
   - Technical / format attributes via `FileValidator` (MediaInfo parsing etc.)
   - Presence and correctness of checksum sidecar (mag) or sequence manifest
     (film) via `ChecksumValidator`.
   - DPX sequence completeness (frame count) via `SequenceValidator`.

High‑level flow (see `main`):
    initialise -> inventory pass (spinner + progress messages) ->
    validation pass (attribute + checksum + sequence) -> summary logging.

Side effects:
    Logs progress and errors, updates several module‑level cumulative lists
    used for the final summary, and prints billboard style status messages.

Exit codes:
    On unrecoverable errors (e.g. no directory chosen, filesystem errors) the
    process exits with a non‑zero status after logging a critical message.

Public entry point:
    Run the module directly to launch the validation workflow.
"""

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
    """Return a test source directory from the environment if configured.

    Looks up the TEST_LOCATION env var (after loading a .env file). If the
    variable exists and is non‑empty the path is returned; otherwise the
    function logs an error and terminates the process.

    Returns:
        str: Absolute or relative path specified in TEST_LOCATION.

    Side Effects:
        Logs errors; may call sys.exit() on failure.
    """
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
    """Prompt the user (native folder chooser) to select a source directory.

    Uses Tkinter's directory selection dialog (raised above other windows).
    Returns the chosen directory path or exits if the user cancels.

    Returns:
        str: User‑selected directory path.

    Side Effects:
        Opens a GUI dialog; logs errors and may terminate the process.
    """
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
    """Initialise logging and select the source location.

    Combines directory selection (interactive) with logger setup and timestamp.

    Returns:
        tuple(datetime, str, logging.Logger): start time, selected location,
            and a module logger instance.
    """
    start_time = datetime.now()
    # location = test_source_location()
    location = set_source_location()
    logging_config.setup_logger()
    logger = logging.getLogger(__name__)

    return start_time, location, logger


def inventory_validation(location, file):
    """Generate inventory metadata for a single file.

    Steps:
        1. Parse file name & type.
        2. Load / parse JSON inventory file if present.
        3. Parse object keys (domain specific metadata derivation).
        4. Write inventory data out (side effect defined by InventoryGenerator).

    Args:
        location (str): Directory path used as the context root.
        file (str): Absolute path (or relative within location) of the file.
    """
    inventory_generator = InventoryGenerator(location, file)
    inventory_generator.parse_file_name_and_type()
    inventory_generator.read_json_inventory()
    inventory_generator.parse_object_keys()
    inventory_generator.write_inventory_data()


def file_attributes_validation(file):
    """Validate technical / format attributes for the given file.

    Args:
        file (str): Path to the media file (DPX or mag).

    Returns:
        bool: True if format attributes are verified, False otherwise.
    """
    file_validator = FileValidator(file)
    file_validator.read_attributes()
    file_validator.format_attributes_validation()

    return file_validator.format_verified


def checksum_validation(file, checksums):
    """Validate a file against a checksum sidecar / manifest.

    Args:
        file (str): Path to the file whose integrity is being checked.
        checksums (str): Path to the checksum sidecar or manifest file.

    Returns:
        bool: True if the file's computed hash matches the manifest entry.
    """
    checksum_validator = ChecksumValidator(file, checksums)
    checksum_validator.generate_file_hash()
    checksum_validator.file_name_extract()
    checksum_validator.seek_in_manifest()
    checksum_validator.validate_checksum()

    return checksum_validator.hash_verified


def dpx_sequence_check(files, path):
    """Run DPX sequence completeness checks for a directory of frames.

    Resolves the expected checksum/manifest file pattern from config, locates
    it, and uses `SequenceValidator` to compare manifest line count with the
    number of DPX frame files present.

    Args:
        files (list[str]): Ordered list of DPX frame file paths.
        path (str): Directory containing the sequence and manifest.

    Returns:
        tuple(list[str], SequenceValidator): The located manifest path(s) and
        the configured validator instance (post counting operations).
    """
    md5 = config.CONFIG["extensions"]["CHECKSUM"]
    checksum_manifest = glob.glob(os.path.join(path, md5))
    sequence_validator = SequenceValidator(files, checksum_manifest[0], path)
    sequence_validator.count_manifest_lines()
    sequence_validator.count_file_sequence()

    return checksum_manifest, sequence_validator


def process_file_inventory(files, path):
    """Process inventory generation for a list of media files.

    Args:
        files (list[str]): File paths to include in inventory.
        path (str): Directory context passed to inventory generation.
    """
    for file in files:
        inventory_validation(path, file)


def process_file_validation(files):
    """Validate format attributes for each file, recording failures.

    Args:
        files (list[str]): Media file paths to validate.
    """
    for file in tqdm(files, desc="MediaInfo"):
        format_verified = file_attributes_validation(file)
        if not format_verified:
            file_attributes_failed.append(file)
        

def mag_checksum_validation(files):
    """Validate checksum sidecars for mag files (one sidecar per file).

    For each file, constructs sidecar filename using configured extension and
    runs checksum comparison if present; logs an error when missing.

    Args:
        files (list[str]): Mag file paths.
    """
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
    """Validate a batch of film (DPX) files against a shared manifest.

    Args:
        files (list[str]): DPX frame file paths.
        checksum_file (str): Path to the manifest containing expected hashes.
    """
    for file in tqdm(files, desc="Checksums"):
        hash_verified = checksum_validation(file, checksum_file)

        if hash_verified:
            checksums_verified.append(file)
        else:
            checksums_failed.append(file)


def main():
    """Module entry point executing the full validation workflow.

    Phases:
        1. Initialise service (logging + start time + directory selection).
        2. Walk tree generating inventory data.
        3. Walk tree validating attributes, DPX sequence integrity, and
           checksums (mag per-file, DPX via manifest).
        4. Log summary statistics.

    Side Effects:
        Performs logging, updates module-level tracking lists, prints status
        messages, and may terminate process on severe errors.
    """
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
