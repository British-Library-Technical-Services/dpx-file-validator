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
            with open(os.path.join(self.write_location, f"dpx_data_report_{self.end_time}.md"), "w") as f:
                f.write(os.path.join(self.report))
        except Exception as e:
            logger.error(f"Error writing report: {e}")
    
    def generate_report(self):

        self.report = f"""
    # DPX DATA REPORT

    * Location: {self.write_location}
    * Started on {self.start_time} 
    * Ended on {self.end_time}
    * Total duration: {self.duration}

    ## Summary
    {self.file_count_report}
    {self.missing_sequence_report}
    {self.checksum_report}
    {self.file_attributes_report}

        """

    def line_count_file_summary(self):
        if self.dpx_files != self.manifest_files:
            self.file_count_report = f"""
    ERROR: number of dpx files in folder != the number listed in the checksum mainfest
    
    * DPX files in folder: {self.dpx_files}
    * DPX files in manifest: {self.manifest_files}
    """

        else:
            self.file_count_report = f"""
    PASS: number of dpx files in folder == number listed in the checksum mainfest:
    
    * DPX files in folder: {self.dpx_files}
    * DPX files in manifest: {self.manifest_files}
    """

    def missing_sequence_summary(self):
        if self.missing_files != []:
            self.missing_sequence_report = f"""
    ERROR: {len(self.missing_files)} missing items from file sequence
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
    ERROR: {len(self.files_failed)} DPX files failed profile validation
    """
            for item in self.files_failed:
                self.file_attributes_report += f"""
    * {item}"""
        else:
            self.file_attributes_report = f"""
    PASS: all files passed DPX profile validation
    """