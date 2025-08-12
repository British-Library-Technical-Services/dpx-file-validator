"""DPX sequence (frame range) validation utilities.

This module exposes `SequenceValidator`, a helper for validating the
integrity of a DPX image sequence against a checksum / register manifest.
Two primary checks are performed:

1. Manifest line count vs. number of DPX files detected in the directory.
2. Detection of gaps in the contiguous frame numbering sequence.

Assumptions:
        * DPX filenames contain an underscore‐delimited frame number token at
            index 5 (zero‑based) when split on "_". Example pattern:
                <BL_><shelfmark><side><file><version>_00001234.dpx
        * The manifest file contains one line per expected frame (sequence).

On mismatch or missing frames, critical log messages are emitted. Missing
frame numbers are accumulated in `missing_sequence`.
"""

import os
import logging

logger = logging.getLogger(__name__)

class SequenceValidator:
    """Validate a DPX sequence against a manifest and internal continuity.

    Args:
        file_list (list[str]): Sorted list of DPX frame file paths.
        manifest (str): Path to the checksum / manifest file.
        path (str): Directory holding the sequence (used for logging context).

    Attributes:
        line_count (int): Number of lines detected in the manifest.
        missing_sequence (list[int]): Frame numbers inferred as missing.
    """
    def __init__(self, file_list, manifest, path):
        self.path = path
        self.file_list = file_list
        self.manifest = manifest
        self.line_count = 0
        self.missing_sequence = []

    def count_manifest_lines(self):
        """Count lines in the manifest and compare to number of DPX files.

        Logs a critical error if counts differ; otherwise logs an info message.
        Updates `line_count` with the number of lines read.
        """
        try:
            with open(self.manifest, 'r') as register:
                self.line_count = sum(1 for count in register)
                
                if self.line_count != len(self.file_list):
                    logger.critical(f"Manifest line count mismatch in {self.path}: line count: {self.line_count} != file count: {len(self.file_list)}")
                else:
                    logger.info(f"Manifest line count match: line count in {self.path}: {self.line_count} == file count: {len(self.file_list)}")

        except FileNotFoundError as e:
            logger.error(f"{self.manifest}, {e}")

    def count_file_sequence(self):
        """Detect gaps in sequential frame numbering.

        Assumes frame number token position as described in module docstring.
        For each file, any intervening missing numbers between the expected
        `sequence_count` and the encountered frame number are logged (critical)
        and appended to `missing_sequence`.
        """
        try:
            if not self.file_list:
                return
            base_count_str = os.path.basename(self.file_list[0]).split("_")[5].split(".")[0]
            sequence_count = int(base_count_str)

            for file_path in self.file_list:
                basename_parts = os.path.basename(file_path).split("_")
                file_count_str = basename_parts[5].split(".")[0]
                target = int(file_count_str)

                while sequence_count < target:
                    self.missing_sequence.append(sequence_count)
                    logger.critical(f"Missing sequence: {basename_parts[1]}: {sequence_count}")
                    sequence_count += 1

                sequence_count += 1

        except (IndexError, ValueError) as e:
            logger.error(f"Sequence parsing error in {self.path}: {e}")
