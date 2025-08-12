"""Console billboard / status message helpers.

Each function prints a simple, formatted multi‑line progress or phase header
used by the DPX validation service to improve readability during long‑running
operations. Functions return no value and have no side effects besides stdout.
"""

def start_service_message():
    """Print the initial banner for the validation service."""
    service_message = """
===| DPX Validation Service |===

Please do not close This window until the service has completed.
"""
    print(service_message)

def inventory_text(path):
    """Print inventory phase header for the supplied root path.

    Args:
        path (str): Directory currently undergoing inventory processing.
    """
    service_message = f"""
Inventory checks in progress for {path}
"""
    print(service_message.strip("\n"))

def validation_text():
    """Print header signaling start of validation (post-inventory) phase."""
    service_message = """
Validation checks in progress:
"""
    print(service_message.strip("\n"))


def mag_files_processing_text(path):
    """Print subsection header for MAG (audio) files within a directory.

    Args:
        path (str): Directory being processed for mag files.
    """
    service_message = f"""
MAG FILES in {path}
"""
    print(service_message.strip("\n"))

def dpx_files_processing_text(path):
    """Print subsection header for DPX (image sequence) files within a directory.

    Args:
        path (str): Directory being processed for DPX files.
    """
    service_message = f"""
DPX FILES in {path}
"""
    print(service_message.strip("\n"))