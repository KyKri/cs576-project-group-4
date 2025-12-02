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
        


class BaseStation:
    def __init__(self, id: int, l1tower: phy.Tower):
        self.tower = l1tower
        self.id = id
        self.active_upload_packets: int = 0
        self.active_download_packets: int = 0
