import asyncio
import logging
from threading import Lock
from typing import Any, Dict, Optional

from aiokafka.structs import RecordMetadata
from kstreams.engine import StreamEngine as Base

logger = logging.getLogger(__name__)


class Singleton(type):
    _instances: Dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class StreamEngine(Base, metaclass=Singleton):
    def __init__(self, *args, **kwargs) -> None:
        # we need the event loop to stop the consumers when the signal
        # is given from the main Thread (django command)
        super().__init__(*args, **kwargs)
        self._stream_task: Optional[asyncio.Future] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = Lock()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
        return self._loop

    async def clean_streams(self) -> None:
        await super().clean_streams()
        self._stream_task = None

    async def _send_patch(
        self,
        topic: str,
        *,
        value: Any = None,
        key: Optional[str] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict] = None,
    ) -> RecordMetadata:
        if self._producer is None:
            await self.start_producer()

        return await self.send(
            topic,
            value=value,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
        )

    def sync_send(
        self,
        topic: str,
        *,
        value: Any = None,
        key: Optional[str] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict] = None,
    ) -> RecordMetadata:
        """
        This method should be called only from a django
        sync context (for example inside a view). In an `async`
        context, normal `send` must be used.
        """
        # we need to make sure that the event loop is free
        # and not running to call the next iteration with sync_send
        # otherwise, it will raise: RuntimeError: This event loop is already running
        with self._lock:
            return self.loop.run_until_complete(
                self._send_patch(
                    topic,
                    value=value,
                    key=key,
                    partition=partition,
                    timestamp_ms=timestamp_ms,
                    headers=headers,
                )
            )

    async def start_streams(self):
        """
        Redefine start_streams to make sure that the event_loop is not closed
        """
        self._stream_task = asyncio.gather(
            *[stream.start() for stream in self._streams]
        )

        try:
            await self._stream_task
        except asyncio.CancelledError:
            await self.stop()
            logger.info("Gracefully Shutdown. Doei")

    def sync_start(self):
        """
        This method only used by the worker in order to start in a synchronous way,
        during testing, the async start is used.
        """
        logger.info("Worker starting...")
        asyncio.run(self.start())

    def sync_stop(self, *args):
        """
        This method only used by the worker in order to stop in a synchronous way.
        When the flag ready_to_stop is set to `Ture` then the stop coroutine will
        stop the engine.

        NOTE: During testing, the async stop is used instead of `sync_stop`.
        """
        assert self._stream_task, "Engine is not running"
        self._stream_task.cancel(msg="Stopping django-streams engine")
