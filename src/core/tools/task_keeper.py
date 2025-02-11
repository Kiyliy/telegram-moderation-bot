import asyncio
from typing import Set, Coroutine, Any

class TaskKeeper:
    def __init__(self):
        self.running_tasks: Set[asyncio.Task] = set()

    def create_task(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self.add_task(task)
        return task

    def add_task(self, task: asyncio.Task) -> None:
        if not isinstance(task, asyncio.Task):
            raise ValueError("Can only add asyncio.Task objects")
        if task not in self.running_tasks:
            self.running_tasks.add(task)
            task.add_done_callback(self._remove_task)

    def _remove_task(self, task: asyncio.Task) -> None:
        self.running_tasks.discard(task)

    async def wait_all(self) -> None:
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)

    def cancel_all(self) -> None:
        for task in self.running_tasks:
            if not task.done():
                task.cancel()

    async def __aenter__(self) -> "TaskKeeper":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cancel_all()
        await self.wait_all()