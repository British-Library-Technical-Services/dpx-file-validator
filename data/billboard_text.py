
def start_service_message():
    service_message = """
===| DPX Validation Service |===

Please do not close This window until the service has completed.
"""
    print(service_message)

def mag_inventory_text():
    service_message = """
Mag file inventory checks in progress:
"""
    print(service_message.strip("\n"))

def film_inventory_text():
    service_message = """
Film scan inventory checks in progress:
"""
    print(service_message.strip("\n"))

def mag_validation_text():
    service_message = """
Mag file validation checks in progress:
"""
    print(service_message.strip("\n"))

def film_validation_text():
    service_message = """
Film scan file validation checks in progress:
"""
    print(service_message.strip("\n"))