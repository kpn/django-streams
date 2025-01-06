import asyncio

import pytest
from django_streaming_example.streaming.engine import stream_engine
from kstreams import TestStreamClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def stream_client():
    return TestStreamClient(stream_engine=stream_engine, monitoring_enabled=False)
