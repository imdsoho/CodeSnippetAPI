import asyncio
import uuid

from fastapi import APIRouter, HTTPException, Request

from eventLoop_processPool.dao import job_model
from eventLoop_processPool.repository import db_repository as database
from eventLoop_processPool.service import jobs


router = APIRouter(prefix="", tags=["Module"])


@router.post("/jobs", response_model=job_model.JobResponse)
async def submit_job(req: job_model.JobRequest, request: Request) -> job_model.JobResponse:
    job_id = uuid.uuid4().hex
    payload = req.model_dump()

    await database.db_insert_job(job_id, payload)

    task = asyncio.create_task(jobs.run_job(job_id, payload, request.app))
    request.app.state.RUNNING_TASKS[job_id] = task

    return job_model.JobResponse(job_id=job_id, status="PENDING")


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    job = await database.db_get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request):
    # 실행 중인 job task가 있으면 취소 시도
    task = request.app.state.RUNNING_TASKS.get(job_id)
    if task and not task.done():
        task.cancel()
        return {"job_id": job_id, "status": "CANCEL_REQUESTED"}

    # 이미 종료된 경우 DB 상태 반환
    job = await database.db_get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job_id": job_id, "status": job["status"]}


@router.post("/jobs_sync")  # 참고: "요청이 끝날 때까지 기다리는" 동기형 엔드포인트
async def submit_and_wait(req: job_model.JobRequest, request: Request):
    """
    클라이언트가 연결을 끊으면 취소하는 패턴을 보여주기 위한 예시.
    운영에서는 /jobs(비동기 제출) + /jobs/{id}(조회) 방식이 보통 더 안전합니다.
    """
    job_id = uuid.uuid4().hex
    payload = req.model_dump()
    await database.db_insert_job(job_id, payload)

    task = asyncio.create_task(jobs.run_job(job_id, payload))
    request.app.state.RUNNING_TASKS[job_id] = task

    try:
        # 연결이 끊겼는지 주기적으로 확인하면서 결과 대기
        while not task.done():
            if await request.is_disconnected():
                task.cancel()
                raise HTTPException(status_code=499, detail="client disconnected; job cancelled")
            await asyncio.sleep(0.1)

        job = await database.db_get_job(job_id)
        return job

    finally:
        request.app.state.RUNNING_TASKS.pop(job_id, None)
