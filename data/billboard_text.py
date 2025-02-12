
def start_service_message():
    service_message = """
===| DPX Validation Service |===

Please do not close This window until the service has completed.
"""
    print(service_message)

def inventory_text(path):
    service_message = f"""
Inventory checks in progress for {path}
"""
    print(service_message.strip("\n"))

def validation_text():
    service_message = """
Validation checks in progress:
"""
    print(service_message.strip("\n"))


def mag_files_processing_text(path):
    service_message = f"""
MAG FILES in {path}
"""
    print(service_message.strip("\n"))

def dpx_files_processing_text(path):
    service_message = f"""
DPX FILES in {path}
"""
    print(service_message.strip("\n"))