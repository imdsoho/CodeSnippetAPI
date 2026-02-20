import asyncio
from eventLoop_processPool.repository import db_repository as database


def cpu_heavy_analyze(payload: dict) -> dict:
    """
    여기 들어가는 코드는 CPU를 오래 쓰는 분석(예: 통계/ML/시뮬레이션 등)을 가정.
    주의: 프로세스에 전달 가능한(피클 가능) 데이터만 사용.
    """
    n = int(payload.get("n", 30_000_000))
    s = 0
    for i in range(n):
        s += (i * i) % 97
    # 분석 결과(예시)
    return {
        "score": s,
        "n": n,
        "meta": payload.get("meta", {}),
    }


async def run_job(job_id: str, payload: dict, app) -> None:
    """
    실제 실행 루틴:
    - DB: RUNNING
    - 세마포어로 동시성 제한
    - event loop에서 run_in_executor로 프로세스에 CPU 작업 위임
    - DB: SUCCEEDED/FAILED/CANCELLED
    """
    assert app.state.EXECUTOR is not None
    assert app.state.CPU_SEM is not None

    loop = asyncio.get_running_loop()
    await database.db_update_status(job_id, "RUNNING")

    try:
        async with app.state.CPU_SEM:
            # CPU-bound는 프로세스 풀로 보냄 (event loop block 방지)
            result = await loop.run_in_executor(app.state.EXECUTOR, cpu_heavy_analyze, payload)
            await database.db_update_status(job_id, "SUCCEEDED", result=result)

    except asyncio.CancelledError:
        # 이 Task 자체가 취소된 경우
        await database.db_update_status(job_id, "CANCELLED", error="Cancelled by client/server")
        raise

    except Exception as e:
        await database.db_update_status(job_id, "FAILED", error=f"{type(e).__name__}: {e}")

    finally:
        app.state.RUNNING_TASKS.pop(job_id, None)
