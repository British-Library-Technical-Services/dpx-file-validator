"""Checksum validation utilities.

This module defines `ChecksumValidator`, a helper class responsible for:
    * Generating an MD5 digest for a supplied file
    * Extracting the filename for matching within a checksum manifest
    * Seeking a matching entry inside a checksum manifest file
    * Comparing the computed digest against the manifest entry and recording
      pass/fail state

The manifest format stores each line beginning with a
32‑character hexadecimal MD5 hash followed by whitespace / filename; the
validator slices the first 32 characters to obtain the expected digest.

Attributes of interest after running the full sequence of methods:
    hash_verified (bool): True if checksum matches manifest entry.
    file_found (bool): True if a line containing the file name was located.
    checksum (str): Hexadecimal MD5 digest computed for the file.

"""

import logging
import os
import hashlib

logger = logging.getLogger(__name__)

class ChecksumValidator:
    """Validate a single file's checksum against a manifest entry.

    Args:
        file (str): Path to the file being validated.
        checksum_manifest (str): Path to the checksum register / manifest file.
    """
    def __init__(self, file, checksum_manifest):

        self.hash_verified = False
        self.file = file
        self.file_name_only = None
        self.checksum_manifest = checksum_manifest
        self.line_count = None
        self.checksum_algorithm = hashlib.md5()
        self.checksum = None
        self.file_found = False
        self.line = None

    def generate_file_hash(self):
        """Compute the MD5 checksum of the target file in streaming chunks.

        Reads the file in 8KB blocks to avoid loading large files fully into
        memory. Stores the resulting 32‑character hex digest in `self.checksum`.
        Logs errors if the file cannot be opened/read.
        """
        self.checksum_algorithm = hashlib.md5()

        try:
            with open(self.file, 'rb') as f:
                while buffer := f.read(8192):
                    self.checksum_algorithm.update(buffer)

                self.checksum = self.checksum_algorithm.hexdigest()
        except FileNotFoundError as e:
            logger.error(f"{self.file}, {e}")

        except (IOError, OSError) as e:
            logger.error(f"{self.file}, {e}")

    def file_name_extract(self):
        """Derive the basename of the file for manifest matching.

        Sets `self.file_name` used in subsequent manifest search.
        """
        try:
            self.file_name = os.path.basename(self.file)
        except FileNotFoundError as e:
            logger.error(f"{self.file}, {e}")

        except (IOError, OSError) as e:
            logger.error(f"{self.file}, {e}")

    def seek_in_manifest(self):
        """Search for the file's basename within the checksum manifest.

        Iterates line by line; if the filename substring appears in a line,
        marks `self.file_found` True and stores the raw line in `self.line`.
        """
        try:
            with open(self.checksum_manifest, 'r') as register:
                for self.line in register:
                    self.line = self.line.strip("\n")
                    if self.file_name in self.line:
                        self.file_found = True
                        break

        except FileNotFoundError as e:
            logger.error(f"{self.file}, {e}")
        except (IOError, OSError) as e:
            logger.error(f"{self.file}, {e}")
        
    def validate_checksum(self):
        """Compare computed checksum against the manifest entry.

        Extracts the first 32 characters of the stored manifest line and performs 
        a case‑insensitive comparison with the
        previously computed checksum. Sets `hash_verified` accordingly and
        logs an error on mismatch.
        """
        line_hash = self.line[:32].casefold() if self.line else None

        if line_hash and line_hash == self.checksum:
            self.hash_verified = True
        else:
            self.hash_verified = False
            logger.error(f"{self.file}, checksums do not match")