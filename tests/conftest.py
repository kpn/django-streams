from dataclasses import field
from typing import Dict, NamedTuple

import pytest
import pytest_asyncio
from kstreams.backends import Kafka

from django_streams.factories import create_engine

AVRO_SCHEMA_V1 = {
    "type": "record",
    "name": "HelloKPN",
    "namespace": "com.kpn.datalab.schemas.example.hello_kpn",
    "fields": [{"name": "message", "type": "string", "default": ""}],
}

AVRO_SCHEMA_V2 = {
    "type": "record",
    "name": "HelloKPN",
    "namespace": "com.kpn.datalab.schemas.example.hello_kpn",
    "fields": [
        {"name": "message", "type": "string", "default": ""},
        {"name": "additional_message", "type": "string", "default": "default"},
    ],
}


class RecordMetadata(NamedTuple):
    offset: int = 1
    partition: int = 1
    topic: str = "my-topic"
    timestamp: int = 1616671352653
    event: Dict = field(default_factory=lambda: {"message": "test"})


@pytest.fixture
def record_metadata():
    return RecordMetadata()


@pytest_asyncio.fixture
async def stream_engine():
    stream_engine = create_engine(
        title="test-engine",
        backend=Kafka(),
    )
    yield stream_engine
    await stream_engine.clean_streams()
    stream_engine.serializer = None
    stream_engine.deserializer = None
