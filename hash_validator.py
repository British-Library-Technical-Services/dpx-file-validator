import logging
import os
import hashlib

logger = logging.getLogger(__name__)

class ChecksumValidator:
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
        try:
            self.file_name = os.path.basename(self.file)
        except FileNotFoundError as e:
            logger.error(f"{self.file}, {e}")

        except (IOError, OSError) as e:
            logger.error(f"{self.file}, {e}")

    def seek_in_manifest(self):
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
            line_hash = self.line[:32].casefold()

            if line_hash == self.checksum:
                self.hash_verified = True
            else:
                self.hash_verified = False
                logger.error(f"{self.file}, checksums do not match")