import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ProcessPoolExecutor

import os
from dataclasses import dataclass
from eventLoop_processPool.repository import db_repository as database
from eventLoop_processPool.web import job_route as job_route


@dataclass
class JobRuntimeConfig:
    max_concurrency: int = 2          # 서버 전체 동시 분석 개수
    max_workers: int = max(os.cpu_count() or 1, 1)


CFG = JobRuntimeConfig(max_concurrency=2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.db_init()
    app.state.EXECUTOR = ProcessPoolExecutor(max_workers=CFG.max_workers)   # None
    app.state.RUNNING_TASKS = {}                                            # RUNNING_TASKS: dict[str, asyncio.Task] = {}
    app.state.CPU_SEM = asyncio.Semaphore(CFG.max_concurrency)              # None

    print(app.state.RUNNING_TASKS)
    print(app.state.CPU_SEM)
    print(app.state.EXECUTOR)

    yield

    if app.state.EXECUTOR:
        app.state.EXECUTOR.shutdown(wait=False, cancel_futures=True)
        EXECUTOR = None


application = FastAPI(lifespan=lifespan)

# CORS Middleware 설정
origins = ["*"]
application.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

application.include_router(job_route.router)


@application.middleware("http")
async def http_request_middleware(request: Request, call_next):
    data_name_list = [request.client.host, request.url.port, request.url, request.url.path, request.method]

    response = await call_next(request)

    return response
