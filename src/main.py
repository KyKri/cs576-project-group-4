from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, confloat
from typing import Literal
import uvicorn
from glu import Glu
import glu
from pathlib import Path

app = FastAPI()
g = Glu()

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

class SimulationConfig(BaseModel):
    height: confloat(gt=0)
    width: confloat(gt=0)
    pixels_per_meter: confloat(gt=0)
    network_type: Literal["LTE_20", "NR_100"]
    starting_ip: str

class BaseStationInit(BaseModel):
    x: float
    y: float

class BaseStationUpdate(BaseModel):
    x: float
    y: float
    on: bool

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

@app.post("/init/simulation")
async def init_simulation(payload: SimulationConfig):
    height = payload.height
    width = payload.width
    pixels_per_meter = payload.pixels_per_meter
    network_type = payload.network_type
    starting_ip = payload.starting_ip

    g.set_tech_profile(network_type)
    g.set_starting_ip(starting_ip)
    g.set_pixels_per_meter(pixels_per_meter)

    return {
        "ok": True,
        "message": "Simulation Initialized",
    }

# Sample call:
"""
curl -X POST http://localhost:8000/init/basestation \
-H "Content-Type: application/json" \
-d '{"x": 100, "y": 100}'
"""
@app.post("/init/basestation")
async def init_basestation(payload: BaseStationInit):
    x = payload.x
    y = payload.y
    bs = g.add_tower(x=x, y=y, on=True)

    return {
        "message": f"BaseStation {bs.id} created successfully",
        "base_station": {
            "id": bs.id,
            "x": bs.tower.x,
            "y": bs.tower.y,
            "on": bs.tower.on,
        },
    }

@app.post("/init/userequipment")
async def init_userequipment(x: float, y: float, ip: str):
    g.add_ue(ip=ip, x=x, y=y)
    return {"message": "Init userequipment received"}

# Sample call
"""
curl -X POST http://localhost:8000/update/basestation/0 \
-H "Content-Type: application/json" \
-d '{"x": 110, "y": 110, "on": false}'
"""
@app.post("/update/basestation/{bs_id}")
async def update_basestation(bs_id: int, payload: BaseStationUpdate):
    x = payload.x
    y = payload.y
    on = payload.on

    updated_bs = None

    for bs in g.base_stations:
        if bs.id == bs_id:
            bs.tower.x = x
            bs.tower.y = y
            bs.tower.on = on
            updated_bs = bs
            break

    if not updated_bs:
        return {"error": f"BaseStation with id {bs_id} not found"}

    return {
        "message": f"BaseStation {bs_id} updated successfully",
        "base_station": {
            "id": updated_bs.id,
            "x": updated_bs.tower.x,
            "y": updated_bs.tower.y,
            "on": updated_bs.tower.on
        }
    }

@app.post("/update/userequipment/{ue_id}")
async def update_userequipment(
    ue_id: int, x: float | None = None, y: float | None = None, ip: str | None = None
):
    for ue in g.ues:
        if ue.id == ue_id:
            if x:
                ue.l1ue.x = x
            if y:
                ue.l1ue.y = y
            if ip:
                ue.ip = ip
            break
    return {"message": "Update userequipment received for {ue_id}"}


@app.websocket("/activity")
async def activity_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


@app.websocket("/packet_transfer")
async def transfer_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        for frame in g.queue:
            _, data = frame
            (src, dst) = glu.extract_ips_from_frame(data)
            await websocket.send_text(f"{src} -> {dst}: {len(data)} bytes")


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
