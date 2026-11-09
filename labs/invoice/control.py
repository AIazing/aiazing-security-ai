"""Evaluator-side lifecycle. Never expose these controls as website endpoints."""

import threading

from .app import LabServer
from .seed import SEED


class InvoiceLab:
    def __init__(self, vulnerable_port=0, fixed_port=0):
        self.servers = {}
        self.threads = []
        self.closed = False
        try:
            self.servers["vulnerable"] = LabServer(vulnerable_port, vulnerable=True)
            self.servers["fixed"] = LabServer(fixed_port, vulnerable=False)
        except BaseException:
            for server in self.servers.values():
                server.server_close()
            raise
        self.ground_truth = SEED

    def start(self):
        if self.closed or self.threads:
            raise RuntimeError("Lab cannot be started in its current state")
        for server in self.servers.values():
            thread = threading.Thread(
                target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
            )
            thread.start()
            self.threads.append(thread)
        return self

    @property
    def urls(self):
        return {
            label: "http://127.0.0.1:{}".format(server.server_port)
            for label, server in self.servers.items()
        }

    def reset(self):
        if self.closed:
            raise RuntimeError("Lab is closed")
        # Call only between assessment runs. Active requests must be quiescent.
        for server in self.servers.values():
            server.store.reset()

    def close(self):
        if self.closed:
            return
        for index, server in enumerate(self.servers.values()):
            if index < len(self.threads):
                server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("Lab worker failed to stop")
        self.closed = True

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.close()
