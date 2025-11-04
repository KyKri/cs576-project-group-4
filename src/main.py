from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
