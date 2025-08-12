"""Reference constants for MediaInfo attribute validation.

This module declares the expected (authoritative) technical metadata values
used to validate WAV (mag audio) and DPX image sequence files. The
`FileValidator` loads MediaInfo JSON output and compares a subset of fields
against these maps:

    wav_validation_map: Ensures audio conforms to preservation profile
        (PCM, 48 kHz, 24-bit).
    dpx_validation_map: Enforces expected DPX characteristics such as version,
        compression mode, endianness, packing, raster dimensions, aspect ratios,
        colour space, bit depth, and lossless compression setting.

`switches` provides the MediaInfo CLI argument instructing JSON output for
parsing.
"""

# MediaInfo output switch for JSON serialization
switches = "--Output=JSON"

# Expected WAV (audio) attributes (MediaInfo audio track fields)
wav_validation_map = {
    "Format":"PCM",
    "SamplingRate":"48000",
    "BitDepth":"24",
}

# Expected DPX (video/image) attributes (MediaInfo video track fields)
dpx_validation_map = {
    "Format":"DPX",
    "Format_Version":"2.0",
    "Format_Compression":"Raw",
    "Format_Settings_Endianness":"Big",
    "Format_Settings_Packing": "Filled A",
    "Width":"2048",
    "Height":"1556",
    "PixelAspectRatio":"1.000",
    "DisplayAspectRatio":"1.316",
    "ColorSpace":"RGB",
    "BitDepth":"10",
    "Compression_Mode":"Lossless",
}