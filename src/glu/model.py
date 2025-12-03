import threading
import layer1 as phy
import layer3 as net

class UE:
    def __init__(self, id: int, l1ue: phy.UE, ip: str):
        self.l1ue = l1ue
        self.id = id
        self.ip = ip
        self.connected_to: BaseStation | None = None
        self.active_upload_packets: int = 0
        self.active_download_packets: int = 0
        self.lock = threading.Lock()

    def inc_upload_packets(self):
        with self.lock:
            self.active_upload_packets += 1

    def dec_upload_packets(self):
        with self.lock:
            self.active_upload_packets -= 1

    def inc_download_packets(self):
        with self.lock:
            self.active_download_packets += 1

    def dec_download_packets(self):
        with self.lock:
            self.active_download_packets -= 1


class BaseStation:
    def __init__(self, id: int, l1tower: phy.Tower):
        self.tower = l1tower
        self.id = id
        self.active_upload_packets: int = 0
        self.active_download_packets: int = 0
        self.lock = threading.Lock()

    def inc_upload_packets(self):
        with self.lock:
            self.active_upload_packets += 1

    def dec_upload_packets(self):
        with self.lock:
            self.active_upload_packets -= 1

    def inc_download_packets(self):
        with self.lock:
            self.active_download_packets += 1

    def dec_download_packets(self):
        with self.lock:
            self.active_download_packets -= 1
