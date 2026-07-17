import pytest
from django_streaming_example.streaming.engine import stream_engine
from kstreams import TestStreamClient


@pytest.fixture
def stream_client():
    return TestStreamClient(stream_engine=stream_engine, monitoring_enabled=False)
