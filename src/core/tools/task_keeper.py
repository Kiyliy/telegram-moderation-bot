import asyncio
from typing import Set, Coroutine, Any

class TaskKeeper:
    _instance = None
    running_tasks: Set[asyncio.Task] = set()
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    @classmethod
    def create_task(cls, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        task = asyncio.create_task(coro)
        cls.add_task(task)
        return task

    @classmethod
    def add_task(cls, task: asyncio.Task) -> None:
        if not isinstance(task, asyncio.Task):
            raise ValueError("Can only add asyncio.Task objects")
        if task not in cls.running_tasks:
            cls.running_tasks.add(task)
            task.add_done_callback(cls._remove_task)

    @classmethod
    def _remove_task(cls, task: asyncio.Task) -> None:
        cls.running_tasks.discard(task)

    @classmethod
    async def wait_all(cls) -> None:
        if cls.running_tasks:
            await asyncio.gather(*cls.running_tasks, return_exceptions=True)

    @classmethod
    def cancel_all(cls) -> None:
        for task in cls.running_tasks:
            if not task.done():
                task.cancel()

    @classmethod
    async def __aenter__(cls) -> "TaskKeeper":
        return cls

    @classmethod
    async def __aexit__(cls, exc_type, exc_val, exc_tb) -> None:
        cls.cancel_all()
        await cls.wait_all()