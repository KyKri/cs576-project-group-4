from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from layer3 import Cabernet

def layer3_example():
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

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class UserEquipment(BaseModel):
    id: int
    ip: str
    coordinates: tuple[int, int]
    signal_quality: float

class BaseStation(BaseModel):
    id: int
    ip: str
    coordinates: tuple[int, int]
    range: int
    power_on: bool

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/control/start")
async def control_start():
    # Logic to start
    return {"message": "Start action received"}

@app.post("/control/pause")
async def control_pause():
    # Logic to pause
    return {"message": "Pause action received"}

@app.post("/control/stop")
async def control_stop():
    # Logic to stop
    return {"message": "Stop action received"}

@app.post("/init/grid")
async def init_grid():
    return {"message": "Init grid received"}

@app.post("/init/basestation")
async def init_basestation():
    return {"message": "Init basestation received"}

@app.post("/init/userequipment")
async def init_userequipment():
    return {"message": "Init userequipment received"}

@app.post("/update/basestation/{bs_id}")
async def update_basestation():
    return {"message": "Update basestation received for {bs_id}"}

@app.post("/update/userequipment/{ue_id}")
async def update_userequipment():
    return {"message": "Update userequipment received for {ue_id}"}

@app.websocket("/activity")
async def activity_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
