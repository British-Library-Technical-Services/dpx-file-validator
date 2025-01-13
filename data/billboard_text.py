
def start_service_message():
    service_message = """
===| DPX Validation Service |===

Please do not close This window until the service has completed.
"""
    print(service_message)

def mag_file_progress():
    service_message = """
WAV file validation checks in progress:
"""
    print(service_message.strip("\n"))

def film_file_progress():
    service_message = """
DPX file validation checks in progress:
"""
    print(service_message.strip("\n"))