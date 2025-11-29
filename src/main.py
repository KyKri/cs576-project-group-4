from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, confloat
from pathlib import Path
from typing import Literal
import uvicorn
from src.glu import Glu
from src import glu

app = FastAPI()
g = Glu()

app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)

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


class UserEquipmentInit(BaseModel):
    x: float
    y: float


class UserEquipmentUpdate(BaseModel):
    x: float
    y: float
    change_ip: bool


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/control/start")
async def control_start():
    # Logic to start
    g.toggle_pause()
    return {"message": "Start action received"}


@app.post("/control/pause")
async def control_pause():
    # Logic to pause
    g.toggle_pause()
    return {"message": "Pause action received"}


@app.post("/control/stop")
async def control_stop():
    # Logic to stop
    g.toggle_pause()
    return {"message": "Stop action received"}


@app.post("/init/simulation")
async def init_simulation(payload: SimulationConfig):
    height = payload.height
    width = payload.width
    pixels_per_meter = payload.pixels_per_meter
    network_type = payload.network_type
    starting_ip = payload.starting_ip

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
    g.syncronize_map()

    return {
        "message": f"BaseStation {bs.id} created successfully",
        "base_station": {
            "id": bs.id,
            "x": bs.tower.x,
            "y": bs.tower.y,
            "on": bs.tower.on,
        },
    }


# Sample call:
"""
curl -X POST http://localhost:8000/init/userequipment \
-H "Content-Type: application/json" \
-d '{"x": 150, "y": 150}'
"""


@app.post("/init/userequipment")
async def init_userequipment(payload: UserEquipmentInit):
    x = payload.x
    y = payload.y

    ue = g.add_ue(x=x, y=y)
    g.syncronize_map()
    bs = -1
    if ue.connected_to is not None:
        bs = ue.connected_to.id

    return {
        "message": f"UserEquipment {ue.id} created successfully",
        "user_equipment": {
            "id": ue.id,
            "x": ue.l1ue.x,
            "y": ue.l1ue.y,
            "ip": ue.ip,
            "bs": bs,
        },
    }


@app.post("/get/basestation/{bs_id}")
async def get_basestation(bs_id: int):
    bs = g.get_tower(bs_id)
    return {
        "base_station": {
            "id": bs.id,
            "x": bs.tower.x,
            "y": bs.tower.y,
            "on": bs.tower.on,
        }
    }


@app.post("/get/userequipment/{ue_id}")
async def get_userequipment(ue_id: int):
    ue = g.get_ue(ue_id)

    bs = -1
    if ue.connected_to is not None:
        bs = ue.connected_to.id

    return {
        "user_equipment": {
            "id": ue.id,
            "x": ue.l1ue.x,
            "y": ue.l1ue.y,
            "ip": ue.ip,
            "bs": bs,
        }
    }


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
            g.syncronize_map()
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
            "on": updated_bs.tower.on,
        },
    }


# Sample call:
"""
curl -X POST http://localhost:8000/update/userequipment/0 \
-H "Content-Type: application/json" \
-d '{"x": 250, "y": 250, "change_ip": false}'
"""


@app.post("/update/userequipment/{ue_id}")
async def update_userequipment(ue_id: int, payload: UserEquipmentUpdate):
    x = payload.x
    y = payload.y
    change_ip = payload.change_ip

    updated_ue = None

    for ue in g.ues:
        if ue.id == ue_id:
            ue.l1ue.x = x
            ue.l1ue.y = y
            if change_ip:
                g.update_ue_ip(ue.id)
            g.syncronize_map()
            updated_ue = ue
            break

    if not updated_ue:
        return {"error": f"UserEquipment with id {ue_id} not found"}

    bs = -1
    if updated_ue.connected_to is not None:
        bs = updated_ue.connected_to.id

    return {
        "message": f"UserEquipment {ue_id} updated successfully",
        "user_equipment": {
            "id": updated_ue.id,
            "x": updated_ue.l1ue.x,
            "y": updated_ue.l1ue.y,
            "ip": updated_ue.ip,
            "bs": bs,
        },
    }


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
        for packet in g.upload_queue._queue:
            frame = packet.frame
            (src, dst) = glu.extract_ips_from_frame(frame)
            await websocket.send_text(f"{src} -> {dst}: {len(frame)} bytes")


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
