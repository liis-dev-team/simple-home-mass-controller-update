import asyncio
from typing import Any, Awaitable, Callable, Iterable

from core import colors
from dtos import Config, WorkerResponse


class END_OF_EXECUTION:
    ...


class ExecutorResult:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self) -> WorkerResponse:
        resp = await self.queue.get()
        if resp is END_OF_EXECUTION:
            raise StopAsyncIteration
        return resp


class PoolExecutor:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.sem = asyncio.Semaphore(config.max_pool_size)
        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue()

    def run(
        self,
        func: Callable[[Any, dict | str], Awaitable[WorkerResponse]],
        payload: Iterable[Any],
    ) -> ExecutorResult:
        if self.lock.locked():
            print(colors.red("EXECUTOR ALREADY RUNNING"))
            return
        asyncio.create_task(self.__run_task(func=func, payload=payload))
        return ExecutorResult(queue=self.queue)

    async def __run_task(
        self,
        func: Callable[[dict | str], Awaitable[WorkerResponse]],
        payload: Iterable[Any],
    ):
        async with self.lock:
            tasks = set()
            for p in payload:
                async with self.sem:
                    task = asyncio.create_task(
                        self.__wrapper(func=func, payload=p)
                    )
                    tasks.add(task)
            if tasks:
                await asyncio.wait(tasks)
            await self.queue.put(END_OF_EXECUTION)

    async def __wrapper(
        self,
        func: Callable[[dict | str], Awaitable[WorkerResponse]],
        payload: dict | str,
    ):
        result = await func(payload)
        await self.queue.put(result)
