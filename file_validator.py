import logging
import os
import subprocess
import json
import sys

from dpx_profile_data import switches, validation_map

logger = logging.getLogger(__name__)

class FileValidator:
    def __init__(self, file):

        self.file = file
        self.file_attributes = None
        self.parsed_data = None
        self.format = None
        self.format_version = None
        self.format_compression = None
        self.format_settings_endianness = None
        self.width = None
        self.height = None
        self.pixel_aspect_ratio = None
        self.display_aspect_ratio = None
        self.frame_rate = None
        self.color_space = None
        self.bit_depth = None
        self.compression_mode = None
        self.format_verified = False

    def read_attributes(self):

        command = ["mediainfo", switches, self.file]

        try:
            self.file_attributes = subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            logging.critical(f"MediaInfo failed to process the file {self.file}: {e}")
            print(f"MediaInfo failed to process the file {self.file}. SYSTEM EXIT.")
            sys.exit(1)

        except FileNotFoundError as e:
            logging.critical(f"MediaInfo is not installed or not found in the system PATH: {e}")
            print("MediaInfo is not installed or not found in the system PATH. SYSTEM EXIT.")
            sys.exit(1)

        except (IOError, OSError) as e:
            logging.critical(f"An error occurred while trying to run MediaInfo: {e}")
            print(f"An error occurred while trying to run MediaInfo. SYSTEM EXIT. {e}")
            sys.exit(1)

    def parse_attributes(self):
        try:
            self.parsed_data = json.loads(self.file_attributes)
            self.format_type = self.parsed_data["media"]["track"][1]["Format"]
            self.version = self.parsed_data["media"]["track"][1]["Format_Version"]
            self.compression = self.parsed_data["media"]["track"][1]["Format_Compression"]
            self.endianness = self.parsed_data["media"]["track"][1]["Format_Settings_Endianness"]
            self.packing = self.parsed_data["media"]["track"][1]["Format_Settings_Packing"]
            self.width = self.parsed_data["media"]["track"][1]["Width"]
            self.height = self.parsed_data["media"]["track"][1]["Height"]
            self.pixel_aspect_ratio = self.parsed_data["media"]["track"][1]["PixelAspectRatio"]
            self.display_aspect_ratio = self.parsed_data["media"]["track"][1]["DisplayAspectRatio"]
            self.colour_space = self.parsed_data["media"]["track"][1]["ColorSpace"]
            self.bit_depth = self.parsed_data["media"]["track"][1]["BitDepth"]
            self.compression_mode = self.parsed_data["media"]["track"][1]["Compression_Mode"]

        except AttributeError as e:
            logger.error(f"{self.file}, {e}")

        except json.JSONDecodeError as e:
            logger.error(f"{self.file}, {e}")


    def validate_attributes(self):
        try:
            # print(self.format_type, self.version, self.compression, self.endianness, self.packing, self.width, self.height, self.pixel_aspect_ratio, self.display_aspect_ratio, self.color_space, self.bit_depth, self.compression_mode)
            if (
                self.format_type == validation_map["Format"]
                and self.version == validation_map["Format_Version"]
                and self.compression == validation_map["Format_Compression"]
                and self.endianness == validation_map["Format_Settings_Endianness"]
                and self.packing == validation_map["Format_Settings_Packing"]
                and self.width == validation_map["Width"]
                and self.height == validation_map["Height"]
                and self.pixel_aspect_ratio == validation_map["PixelAspectRatio"]
                and self.display_aspect_ratio == validation_map["DisplayAspectRatio"]
                and self.colour_space == validation_map["ColorSpace"]
                and self.bit_depth == validation_map["BitDepth"]
                and self.compression_mode == validation_map["Compression_Mode"]
            ):
                self.format_verified = True
            else:
                self.format_verified = False
        
        except IndexError as e:
            logger.error(f"{self.file}, {e}")

        except KeyError as e:
            logger.error(f"{self.file}, {e}")
