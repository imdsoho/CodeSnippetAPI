import asyncio
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional


DB_PATH = os.environ.get("JOB_DB_PATH", "jobs.sqlite3")


def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def _db_init() -> None:
    conn = _db_connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            result_json TEXT,
            error_text TEXT
        )
        """
    )
    conn.commit()
    conn.close()


async def db_init() -> None:
    await asyncio.to_thread(_db_init)


def _db_insert_job(job_id: str, payload: dict) -> None:
    now = datetime.utcnow().isoformat()
    conn = _db_connect()
    conn.execute(
        """
        INSERT INTO jobs (job_id, status, created_at, updated_at, payload_json, result_json, error_text)
        VALUES (?, ?, ?, ?, ?, NULL, NULL)
        """,
        (job_id, "PENDING", now, now, json.dumps(payload)),
    )
    conn.commit()
    conn.close()


async def db_insert_job(job_id: str, payload: dict) -> None:
    await asyncio.to_thread(_db_insert_job, job_id, payload)


def _db_update_status(job_id: str, status: str, result: Optional[dict] = None, error: Optional[str] = None) -> None:
    now = datetime.utcnow().isoformat()
    conn = _db_connect()
    conn.execute(
        """
        UPDATE jobs
        SET status=?, updated_at=?, result_json=?, error_text=?
        WHERE job_id=?
        """,
        (status, now, json.dumps(result) if result is not None else None, error, job_id),
    )
    conn.commit()
    conn.close()


async def db_update_status(job_id: str, status: str, result: Optional[dict] = None, error: Optional[str] = None) -> None:
    await asyncio.to_thread(_db_update_status, job_id, status, result, error)


def _db_get_job(job_id: str) -> Optional[dict]:
    conn = _db_connect()
    cur = conn.execute(
        "SELECT job_id, status, created_at, updated_at, payload_json, result_json, error_text FROM jobs WHERE job_id=?",
        (job_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "job_id": row[0],
        "status": row[1],
        "created_at": row[2],
        "updated_at": row[3],
        "payload": json.loads(row[4]),
        "result": json.loads(row[5]) if row[5] else None,
        "error": row[6],
    }


async def db_get_job(job_id: str) -> Optional[dict]:
    return await asyncio.to_thread(_db_get_job, job_id)
