import signal
import threading


class GracefulLifecycle:
    def __init__(self):
        self.stop_event = threading.Event()

    def request_stop(self, *_):
        self.stop_event.set()

    def install_signal_handlers(self):
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)

    def should_stop(self):
        return self.stop_event.is_set()
