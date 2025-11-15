from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, confloat
from typing import Literal
import uvicorn
from glu import Glu
import glu

app = FastAPI()
g = Glu()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

class SimulationConfig(BaseModel):
    height: confloat(gt=0)
    width: confloat(gt=0)
    pixels_per_meter: confloat(gt=0)
    network_type: Literal["LTE_20", "NR_100"]
    starting_ip: str

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

@app.post("/init/basestation")
async def init_basestation(x: float, y: float):
    g.add_tower(x=x, y=y, on=True)

    return {"message": "Init basestation received"}


@app.post("/init/userequipment")
async def init_userequipment(x: float, y: float, ip: str):
    g.add_ue(ip=ip, x=x, y=y)
    return {"message": "Init userequipment received"}


@app.post("/update/basestation/{bs_id}")
async def update_basestation(
    bs_id: int, x: float | None = None, y: float | None = None, on: bool | None = None
):
    for bs in g.base_stations:
        if bs.id == bs_id:
            if x:
                bs.tower.x = x
            if y:
                bs.tower.y = y
            if on:
                bs.tower.on = on
            break
    return {"message": "Update basestation received for {bs_id}"}


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
