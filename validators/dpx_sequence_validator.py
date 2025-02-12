import os
import logging

logger = logging.getLogger(__name__)

class SequenceValidator:
    def __init__(self, file_list, manifest, path):
        self.path = path
        self.file_list = file_list
        self.manifest = manifest
        self.line_count = 0
        self.missing_sequence = []

    def count_manifest_lines(self):
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
        try:
            base_count = os.path.basename(self.file_list[0]).split("_")[5].split(".")[0]
            sequence_count = int(base_count)
        
            for count in self.file_list:
                basename = os.path.basename(count).split("_")
                file_count = basename[5].split(".")[0]
                
                while sequence_count < int(file_count):
                    self.missing_sequence.append(sequence_count)
                    logger.critical(f"Missing sequence: {basename[1]}: {sequence_count}")
                    sequence_count += 1
                
                sequence_count += 1
            
        except IndexError as e:
            logger.error(f"{count}, {e}")
