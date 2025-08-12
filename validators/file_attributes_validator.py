"""File attribute validation using MediaInfo output.

This module defines `FileValidator`, a helper that executes MediaInfo (JSON
output mode) against DPX image files and WAV audio (mag) files and validates
selected technical metadata fields against expected reference values defined
in the data model maps (`dpx_validation_map`, `wav_validation_map`).

Workflow (typical):
    v = FileValidator(path_to_file)
    v.read_attributes()                 # runs MediaInfo -> raw JSON bytes
    v.format_attributes_validation()    # parses, dispatches, validates
    if v.format_verified:
        ...

Validation logic is format‑specific:
    * WAV: SamplingRate, BitDepth
    * DPX: Version, Compression, Endianness, Packing, Width, Height,
      PixelAspectRatio, DisplayAspectRatio, ColorSpace, BitDepth,
      Compression_Mode

On failure a critical log is emitted and `format_verified` remains False.
Fatal issues launching MediaInfo trigger a process exit
"""

import logging
import os
import subprocess
import json
import sys

from data.file_attributes_model import switches, dpx_validation_map, wav_validation_map

logger = logging.getLogger(__name__)


class FileValidator:
    """Validate media file technical attributes against known profiles.

    Args:
        file (str): Path to the target media file (DPX or WAV).
    """
    def __init__(self, file):

        self.file = file
        self.file_attributes = None
        self.parsed_data = None
        self.format = None
        self.sample_rate = None
        self.bit_depth = None
        self.format_version = None
        self.format_compression = None
        self.format_settings_endianness = None
        self.width = None
        self.height = None
        self.pixel_aspect_ratio = None
        self.display_aspect_ratio = None
        self.frame_rate = None
        self.color_space = None
        self.compression_mode = None
        self.format_verified = False

    def read_attributes(self):
        """Run MediaInfo with predefined switches and capture JSON output.

        Side Effects:
            Populates `self.file_attributes` (raw JSON bytes).
            Exits process on fatal MediaInfo invocation errors.
        """

        command = ["mediainfo", switches, self.file]

        try:
            self.file_attributes = subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            logging.critical(f"MediaInfo failed to process the file {self.file}: {e}")
            print(f"MediaInfo failed to process the file {self.file}. SYSTEM EXIT.")
            sys.exit(1)

        except FileNotFoundError as e:
            logging.critical(
                f"MediaInfo is not installed or not found in the system PATH: {e}"
            )
            print(
                "MediaInfo is not installed or not found in the system PATH. SYSTEM EXIT."
            )
            sys.exit(1)

        except (IOError, OSError) as e:
            logging.critical(f"An error occurred while trying to run MediaInfo: {e}")
            print(f"An error occurred while trying to run MediaInfo. SYSTEM EXIT. {e}")
            sys.exit(1)

    def wav_file_attributes(self):
        """Extract WAV attribute subset (sampling rate, bit depth) from JSON."""
        self.sample_rate = self.parsed_data["media"]["track"][1]["SamplingRate"]
        self.bit_depth = self.parsed_data["media"]["track"][1]["BitDepth"]

    def dpx_file_attributes(self):
        """Extract DPX attribute subset required for validation from JSON."""
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

    def format_attributes_validation(self):
        """Parse MediaInfo JSON and perform format‑specific validation.

        Determines file format (DPX/WAV) then delegates extraction and
        validation steps. Sets `format_verified` when all expected fields
        match reference values.
        """
        try:
            self.parsed_data = json.loads(self.file_attributes)
            self.format_type = self.parsed_data["media"]["track"][1]["Format"]

            if self.format_type == wav_validation_map["Format"]:
                self.wav_file_attributes()
                self.wav_validate_attributes()
            elif self.format_type == dpx_validation_map["Format"]:
                self.dpx_file_attributes()
                self.dpx_validate_attributes()

        except AttributeError as e:
            logger.error(f"{self.file}, {e}")

        except json.JSONDecodeError as e:
            logger.error(f"{self.file}, {e}")

    def wav_validate_attributes(self):
        """Validate extracted WAV attributes against reference map."""
        try:
            if (
                self.sample_rate == wav_validation_map["SamplingRate"]
                and self.bit_depth == wav_validation_map["BitDepth"]
            ):
                self.format_verified = True
            else:
                self.format_verified = False
                logger.critical(f"File attribues did not validate {self.file}")

        except IndexError as e:
            logger.error(f"{self.file}, {e}")

        except KeyError as e:
            logger.error(f"{self.file}, {e}")

    def dpx_validate_attributes(self):
        """Validate extracted DPX attributes against reference map."""
        try:
            if (
                self.version == dpx_validation_map["Format_Version"]
                and self.compression == dpx_validation_map["Format_Compression"]
                and self.endianness == dpx_validation_map["Format_Settings_Endianness"]
                and self.packing == dpx_validation_map["Format_Settings_Packing"]
                and self.width == dpx_validation_map["Width"]
                and self.height == dpx_validation_map["Height"]
                and self.pixel_aspect_ratio == dpx_validation_map["PixelAspectRatio"]
                and self.display_aspect_ratio == dpx_validation_map["DisplayAspectRatio"]
                and self.colour_space == dpx_validation_map["ColorSpace"]
                and self.bit_depth == dpx_validation_map["BitDepth"]
                and self.compression_mode == dpx_validation_map["Compression_Mode"]
            ):
                self.format_verified = True
            else:
                self.format_verified = False
                logger.critical(f"File attribues did not validate {self.file}")

        except IndexError as e:
            logger.error(f"{self.file}, {e}")

        except KeyError as e:
            logger.error(f"{self.file}, {e}")
