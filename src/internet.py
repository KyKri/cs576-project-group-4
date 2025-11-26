import os
from layer3 import Cabernet


c = Cabernet().with_internet("10.0.0.5", "10.0.0.0/24")
c.create_ue("10.0.0.4")
c.create_ue("10.0.0.3")

try:
    while True:
        frame = c.poll_frame()
        if frame is None:
            continue

        # print(f"Frame polled: {len(frame)} bytes")
        src = frame[16:20]
        dst = frame[20:24]
        src = ".".join(map(str, src))
        dst = ".".join(map(str, dst))
        print(f"{src} -> {dst}")

        if os.path.exists("/pause"):
            continue

        try:
            c.send_frame(frame)
        except Exception as e:
            print(f"Error sending frame: {e}")
except KeyboardInterrupt:
    print("cleaning up...")
    del c
    print("Exiting...")
