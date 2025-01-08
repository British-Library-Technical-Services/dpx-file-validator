import logging
import os

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, write_location, start_time, end_time, duration, dpx_files, manifest_files, missing_files, files_failed, checksums_verified, checksums_failed):
        self.write_location = write_location
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.dpx_files = dpx_files
        self.first_file = dpx_files[0].split("/")[-1]
        self.last_file = dpx_files[-1].split("/")[-1]
        self.manifest_files = manifest_files
        self.missing_files = missing_files
        self.files_failed = files_failed
        self.checksums_verified = checksums_verified
        self.checksums_failed = checksums_failed
        # self.total_size = total_size

        self.file_count_report = None
        self.missing_sequence_report = None
        self.file_attributes_report = None
        self.checksum_report = None
        self.report = None

    def write_report(self):

        try:
            with open(os.path.join(self.write_location, f"dpx_data_report_{self.end_time}.md"), "w", encoding=("utf-8")) as f:
                f.write(os.path.join(self.report))
        except Exception as e:
            logger.error(f"Error writing report: {e}")
    
    def generate_report(self):

        self.report = f"""
# DPX DATA REPORT

## Report Summary
* Shelfmark: 
* Location: {self.write_location}
* Started on {self.start_time} 
* Ended on {self.end_time}
* Total duration: {self.duration}

## File Count
{self.file_count_report}
## Sequence Validation
* First file in sequence: {self.first_file}
* Last file in sequence: {self.last_file}
{self.missing_sequence_report}
## Checksum Validation
{self.checksum_report}
## File Attributes Validation
{self.file_attributes_report}

        """

    def line_count_file_summary(self):
        if self.dpx_files != self.manifest_files:
            self.file_count_report = f""" 
* DPX files in folder: {len(self.dpx_files)}
* DPX files in manifest: {self.manifest_files}

ERROR: number of dpx files in folder != the number listed in the checksum mainfest
    """

        else:
            self.file_count_report = f"""    
* DPX files in folder: {self.dpx_files}
* DPX files in manifest: {self.manifest_files}

PASS: number of dpx files in folder == number listed in the checksum mainfest
    """

    def missing_sequence_summary(self):
        if self.missing_files != []:
            self.missing_sequence_report = f"""
ERROR: {len(self.missing_files)} missing items from file sequence.  See log for complete list.
    """
            for item in self.missing_files:
                self.missing_sequence_report += f"""
* {item}"""
        else:
            self.missing_sequence_report = f"""
PASS: no missing items from file sequence 
    """
    
    def checksum_summary(self):
        if self.checksums_failed != []:
            self.checksum_report = f"""
ERROR: {len(self.checksums_failed)} checksums failed
    """
            for item in self.checksums_failed:
                self.checksum_report += f"""
* {item}"""
        else:
            self.checksum_report = f"""
PASS: all checksums verified
    """
    
    def file_attributes_summary(self):
        if self.files_failed != []:
            self.file_attributes_report = f"""
ERROR: {len(self.files_failed)} DPX files failed profile validation.  See log for complete list.
    """
            for item in self.files_failed:
                self.file_attributes_report += f"""
* {item}"""
        else:
            self.file_attributes_report = f"""
PASS: all files passed DPX profile validation
    """