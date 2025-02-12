import sys
import threading
import itertools
import time

class Spinner:
    def __init__(self):
        self.spinner = itertools.cycle(['/', '-', '\\', '|'])
        self.running = False
        self.spinner_thread = None

    def spin(self):
        while self.running:
            sys.stdout.write(next(self.spinner))
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('\b')

    def start(self):
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.start()

    def stop(self):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()
