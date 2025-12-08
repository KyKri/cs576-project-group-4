import threading
import random
import time
import heapq
from queue import Queue
from typing import Tuple

from typing import List
from .model import UE, BaseStation


class Packet:
    def __init__(
        self,
        arrival_time: float,
        frame: bytes,
        packet_error_rate: float,
        src: UE | BaseStation | None,
        dst: UE | BaseStation | None,
    ):
        self.arrival_time = arrival_time
        self.frame = frame
        self.packet_error_rate = packet_error_rate
        self.src = src
        self.dst = dst
        if self.src:
            self.src.inc_upload_packets()
        if self.dst:
            self.dst.inc_download_packets()

    def is_corrupted(self) -> bool:
        return random.random() < self.packet_error_rate

    def has_arrived(self) -> bool:
        return time.time() * 1000 >= self.arrival_time

    def deliver(self):
        if self.src:
            self.src.dec_upload_packets()
        if self.dst:
            self.dst.dec_download_packets()

    def __lt__(self, other: "Packet") -> bool:
        return self.arrival_time < other.arrival_time


class PacketQueue:
    def __init__(self):
        self._queue: List[Packet] = []
        # self._queue=Queue()
        self._lock = threading.Lock()

    def enqueue(self, item: Packet):
        # self._queue.put(item)
        heapq.heappush(self._queue, item)

    def pop_arrived(self) -> List[Packet]:
        matched: List[Packet] = []

        while len(self._queue) > 0 and self._queue[0].has_arrived():
        # while self._queue.qsize() > 0 and self._queue.queue[0].has_arrived():
            item = heapq.heappop(self._queue)
            # item = self._queue.get()
            matched.append(item)
        return matched

    def next_ready_timeout(self) -> Tuple[bool, float | None]:
        if len(self._queue) == 0:
        # if self._queue.empty():
            return True, None
        # timeout_ms = self._queue.queue[0].arrival_time - time.time() * 1000
        timeout_ms = self._queue[0].arrival_time - time.time() * 1000
        if timeout_ms < 10:
            return False, None
        return True, timeout_ms / 1000
