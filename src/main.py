from layer3 import Cabernet

c=Cabernet()
c.create_ue("10.0.0.4")
c.create_ue("10.0.0.5")

i=0
while True:
    frame = c.poll_frame()
    if frame is None:
        continue

    i+=1
    # simulate 5% packet loss
    if i % 20 == 0:
        continue
        
    try:
        c.send_frame(frame)
    except Exception as e:
        print(f"Error sending frame: {e}")
