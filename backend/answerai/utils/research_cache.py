"""Bounded, short-lived public-search caching, scoped to the authenticated user."""

import asyncio
import time
from collections import OrderedDict


class SearchCache:
    def __init__(self, capacity=128, ttl=60):
        self.capacity = capacity
        self.ttl = ttl
        self.values = OrderedDict()
        self.pending = {}
        self.lock = asyncio.Lock()
        self.slots = asyncio.Semaphore(16)

    async def get(self, key, load):
        async with self.lock:
            entry = self.values.get(key)
            if entry and entry[0] > time.monotonic():
                self.values.move_to_end(key)
                return entry[1]
            self.values.pop(key, None)
            task = self.pending.get(key)
            if task is None:
                if len(self.pending) >= self.capacity:
                    raise RuntimeError('Search is busy; retry after current requests finish.')
                task = asyncio.create_task(self._load(key, load))
                self.pending[key] = task
                task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        return await asyncio.shield(task)

    async def _load(self, key, load):
        try:
            async with asyncio.timeout(50):
                async with self.slots:
                    result = await load()
            async with self.lock:
                self.values[key] = (time.monotonic() + self.ttl, result)
                while len(self.values) > self.capacity:
                    self.values.popitem(last=False)
            return result
        finally:
            async with self.lock:
                self.pending.pop(key, None)


PUBLIC_SEARCH_CACHE = SearchCache()
