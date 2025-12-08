import asyncio
import logging
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import WebSocketDisconnect
from pydantic import BaseModel, confloat
from pathlib import Path
from typing import Literal
import uvicorn
from glu import Glu, extract_ips_from_frame
import layer1 as phy

LOG_FORMAT = "%(levelname)s:\t[%(filename)s:%(lineno)d]:\t%(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create your logger
logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)

g = Glu()
app = FastAPI()


app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


class SimulationConfig(BaseModel):
    height: confloat(gt=0)
    width: confloat(gt=0)
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


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("ArshiA Shutting down...")
    global g
    del g.cabernet
    import gc

    gc.collect()
    logger.info("glu dropped")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/control/pause")
async def control_pause():
    g.toggle_pause()
    return {"paused": g.paused}


@app.post("/control/drop")
async def control_drop():
    g.toggle_drop()
    return {"drop": g.dropping_packets}


@app.post("/control/delay")
async def control_delay():
    g.toggle_delay()
    return {"delay": g.delaying_packets}


@app.post("/init/simulation")
async def init_simulation():
    # g.run(log_to_sdout=False)
    g.run_single_threaded()
    g.toggle_pause()  # unpause
    return {"ok": True, "message": "Simulation initialized", "paused": g.paused}


@app.post("/configure")
async def configure(payload: SimulationConfig):
    network_type = payload.network_type
    if network_type == "LTE_20":
        tech = phy.LTE_20
    else:
        tech = phy.NR_100
    for bs in g.base_stations:
        bs.tower.t = tech

    return {
        "ok": True,
        "message": "Simulation configured",
    }


# Sample call:
"""
curl -X POST http://localhost:8000/init/basestation \
-H "Content-Type: application/json" \
-d '{"x": 100, "y": 100}'
"""


@app.post("/init/basestation")
async def init_basestation(payload: BaseStationInit):
    x = payload.x / g.pixels_per_meter
    y = payload.y / g.pixels_per_meter
    bs = g.add_tower(x=x, y=y, on=True)
    g.syncronize_map()

    return {
        "message": f"Base Station {bs.id} created successfully",
        "base_station": {
            "id": bs.id,
            "x": bs.tower.x * g.pixels_per_meter,
            "y": bs.tower.y * g.pixels_per_meter,
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
    x = payload.x / g.pixels_per_meter
    y = payload.y / g.pixels_per_meter

    ue = g.add_ue(x=x, y=y)
    g.syncronize_map()
    bs = -1
    if ue.connected_to is not None:
        bs = ue.connected_to.id

    return {
        "message": f"User Equipment {ue.id} created successfully",
        "user_equipment": {
            "id": ue.id,
            "x": ue.l1ue.x * g.pixels_per_meter,
            "y": ue.l1ue.y * g.pixels_per_meter,
            "ip": ue.ip,
            "bs": bs,
            "up_packets": ue.active_upload_packets,
            "down_packets": ue.active_download_packets,
        },
    }


@app.get("/get/basestation/{bs_id}")
async def get_basestation(bs_id: int):
    bs = g.get_tower(bs_id)
    return {
        "base_station": {
            "id": bs.id,
            "x": bs.tower.x * g.pixels_per_meter,
            "y": bs.tower.y * g.pixels_per_meter,
            "on": bs.tower.on,
        }
    }


@app.get("/get/userequipment/{ue_id}")
async def get_userequipment(ue_id: int):
    ue = g.get_ue(ue_id)

    bs = -1
    if ue.connected_to is not None:
        bs = ue.connected_to.id

    return {
        "user_equipment": {
            "id": ue.id,
            "x": ue.l1ue.x * g.pixels_per_meter,
            "y": ue.l1ue.y * g.pixels_per_meter,
            "ip": ue.ip,
            "bs": bs,
            "up_packets": ue.active_upload_packets,
            "down_packets": ue.active_download_packets,
        }
    }


@app.get("/check/userequipment/{ue_id}")
async def check_userequipment(ue_id: int):
    ue = g.get_ue(ue_id)

    return {
        "id": ue.id,
        "up_packets": ue.active_upload_packets,
        "down_packets": ue.active_download_packets,
    }


@app.get("/check/link/{ue_id}")
async def check_link(ue_id: int):
    ue = g.get_ue(ue_id)
    l1ue = ue.l1ue
    nbytes = 1024
    # assumes that UE is already connected to base station.
    # function should not call if UE is not connected to a base station
    bs = ue.connected_to

    up_latency = bs.tower.upload_latency(l1ue, nbytes, g.active_ues())
    dn_latency = bs.tower.download_latency(l1ue, nbytes, g.active_towers())
    up_bandwidth = bs.tower.upload_bandwidth_mbps(l1ue, g.active_ues())
    dn_bandwidth = bs.tower.download_bandwidth_mbps(l1ue, g.active_towers())
    up_packeterr = bs.tower.upload_packet_error_rate(l1ue, nbytes, g.active_ues())
    dn_packeterr = bs.tower.download_packet_error_rate(l1ue, nbytes, g.active_towers())

    return {
        "upload_latency": up_latency,
        "download_latency": dn_latency,
        "upload_bandwidth": up_bandwidth,
        "download_bandwidth": dn_bandwidth,
        "upload_per": up_packeterr,
        "download_per": dn_packeterr,
    }


# Sample call
"""
curl -X POST http://localhost:8000/update/basestation/0 \
-H "Content-Type: application/json" \
-d '{"x": 110, "y": 110, "on": false}'
"""


@app.post("/update/basestation/{bs_id}")
async def update_basestation(bs_id: int, payload: BaseStationUpdate):
    x = payload.x / g.pixels_per_meter
    y = payload.y / g.pixels_per_meter
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
            "x": updated_bs.tower.x * g.pixels_per_meter,
            "y": updated_bs.tower.y * g.pixels_per_meter,
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
    x = payload.x / g.pixels_per_meter
    y = payload.y / g.pixels_per_meter
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
            "x": updated_ue.l1ue.x * g.pixels_per_meter,
            "y": updated_ue.l1ue.y * g.pixels_per_meter,
            "ip": updated_ue.ip,
            "bs": bs,
        },
    }


@app.websocket("/packet_transfer")
async def transfer_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Websocket Listening")
    try:
        await log_packets(websocket)
    except WebSocketDisconnect:
        logger.warning("WebSocket client disconnected")
    except asyncio.CancelledError:
        logger.info("WebSocket handler cancelled (probably Ctrl+C / shutdown)")


async def log_packets(websocket: WebSocket):
    # You can keep or drop this greeting, up to you
    await websocket.send_text("Log Packet Greeting")

    while True:
        try:
            qsize = g.log_queue.qsize()
            if qsize == 0:
                packet = await asyncio.to_thread(g.log_queue.get)
                frame = packet.frame
                src, dst = extract_ips_from_frame(frame)
                message = f"{src} -> {dst}: {len(frame)} bytes\n"
                await websocket.send_text(message)
                continue
            packets = [g.log_queue.get() for _ in range(qsize)]
            message = ""
            for packet in packets:
                frame = packet.frame
                src, dst = extract_ips_from_frame(frame)
                message += f"{src} -> {dst}: {len(frame)} bytes\n"
            await websocket.send_text(message)
        except WebSocketDisconnect:
            raise
        except asyncio.CancelledError:
            raise


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
