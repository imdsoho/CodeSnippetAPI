import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Optional
import time


@dataclass
class TaskOutcome:
    name: str
    ok: bool
    value: Any = None
    error: Optional[BaseException] = None


async def _run_named(name: str, coro: Awaitable[Any]) -> TaskOutcome:
    try:
        v = await coro
        return TaskOutcome(name=name, ok=True, value=v)
    except BaseException as e:
        return TaskOutcome(name=name, ok=False, error=e)


async def aggregate_results(
        tasks: Iterable[tuple[str, Awaitable[Any]]],
        *,
        timeout: Optional[float] = None,
) -> dict[str, Any]:
    coros = [_run_named(name, coro) for name, coro in tasks]

    try:
        outcomes = await asyncio.wait_for(asyncio.gather(*coros), timeout=timeout)
    except asyncio.TimeoutError:
        return {"results": {}, "errors": {"__timeout__": "timeout"}, "meta": {"ok": False}}

    results: dict[str, Any] = {}
    errors: dict[str, Any] = {}

    for o in outcomes:
        if o.ok:
            results[o.name] = o.value
        else:
            errors[o.name] = F"{type(o.error).__name__}: {o.error}"

    meta = {
        "ok": len(errors) == 0,
        "n_total": len(list(tasks)) if not isinstance(tasks, Iterable) else len(tasks),
        "n_ok": len(results),
        "n_err": len(errors),
    }

    return {"results": results, "errors": errors, "meta": meta}


async def foo():
    await asyncio.sleep(1)

    return {"foo": 1}


async def bar():
    await asyncio.sleep(2)
    raise ValueError("bad bar")


async def baz():
    await asyncio.sleep(4)

    return {"baz": 1}


async def qux():
    await asyncio.sleep(3)

    return {"qux": 1}


async def main():
    tasks_arr = list()
    tasks_arr.append(("foo", foo()))
    tasks_arr.append(("bar", bar()))
    tasks_arr.append(("baz", baz()))
    tasks_arr.append(("qux", qux()))

    out = await aggregate_results(
        tasks_arr,
        timeout=10.0)
    print(out)


if __name__ == "__main__":
    start = time.perf_counter()

    asyncio.run(main())

    end = time.perf_counter()  # 종료 시간 저장
    print(f"소요 시간: {end - start:.5f}초")
