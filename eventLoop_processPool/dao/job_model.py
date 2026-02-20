import os
from dataclasses import dataclass

from typing import Any, Optional

from pydantic import BaseModel, Field


@dataclass
class JobRuntimeConfig:
    max_concurrency: int = 2          # 서버 전체 동시 분석 개수
    max_workers: int = max(os.cpu_count() or 1, 1)


class JobRequest(BaseModel):
    n: int = Field(default=30_000_000, ge=1, description="CPU-heavy loop size (example)")
    meta: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    job_id: str
    status: str
