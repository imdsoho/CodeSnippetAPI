from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json, uvicorn
from asyncio import sleep
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def waypoints_generator():
    waypoints = open('waypoints.json')
    waypoints = json.load(waypoints)
    for waypoint in waypoints[0: 10]:
        data = json.dumps(waypoint)

        #EventSource.onmessage 에서 사용
        #message = f"id: \nevent: \ndata:{data}\nretry: \n\n"
        #yield message

        #EventSource.addEventListener 에서 "ping" key로 사용
        message = f"id: \nevent: ping\ndata:{data}\nretry: \n\n"
        yield message

        await sleep(1)


@app.get("/get-waypoints")
async def root():
    return StreamingResponse(waypoints_generator(), media_type="text/event-stream")


async def progress_generator():
    progress = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    for rate in progress:
        data = json.dumps({"rate": rate})
        print(data)

        message = f"id: \nevent: state\ndata:{data}\nretry: \n\n"
        yield message

        await sleep(0.5)


@app.get("/get-progress")
async def get_progress():
    return StreamingResponse(progress_generator(), media_type="text/event-stream")


@app.get("/create_heatmap")
def create_heatmap():
    time.sleep(3)

    return "create heatmap"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
