import json
from typing import Any, Dict, Optional
from unittest import mock

import aiokafka
import pytest
from kstreams import ConsumerRecord, Stream, clients, consts, types
from kstreams.streams_utils import UDFType
from kstreams.test_utils.structs import RecordMetadata

from django_streams.engine import StreamEngine
from django_streams.factories import create_engine
from django_streams.test_utils.test_client import TestStreamClient

topic = "dev-kpn-des--hello-world"
value = {"message": "Hi KPN"}
event_type = "hello_world.test"
schema_id = "example/hello_kpn/v0.0.1/schema.avsc"
key = "hello"


class MySerializer:
    async def serialize(
        self,
        payload: Any,
        headers: Optional[types.Headers] = None,
        serializer_kwargs: Optional[Dict] = None,
    ) -> bytes:
        """
        Serialize paylod to json
        """
        value = json.dumps(payload)
        return value.encode()


def test_singlenton():
    assert create_engine() == create_engine()


@pytest.mark.asyncio
async def test_add_streams_no_typing(stream_engine: StreamEngine):
    """
    Test add `stream` in the old fashion
    """
    topic = "dev-kpn-des--hello-kpn"

    @stream_engine.stream(topic)
    async def stream(stream):
        assert isinstance(stream, Stream)

    with mock.patch("kstreams.clients.Consumer.start") as mock_consumer_start:
        await stream_engine.start_streams()
        mock_consumer_start.assert_called()
        stream_instance = stream_engine._streams[0]

        assert stream_instance == stream
        assert stream_instance.topics == [topic]
        assert stream_instance.udf_handler.type == UDFType.NO_TYPING


@pytest.mark.asyncio
async def test_add_streams_with_typing(stream_engine: StreamEngine):
    topic = "dev-kpn-des--hello-kpn"

    @stream_engine.stream(topic)
    async def stream_one(cr: ConsumerRecord):
        ...

    @stream_engine.stream(topic)
    async def stream_two(cr: ConsumerRecord, stream: Stream):
        ...

    with (
        mock.patch("aiokafka.AIOKafkaConsumer.start") as mock_consumer_start,
        mock.patch(
            "kstreams.streams.Stream.func_wrapper_with_typing"
        ) as mock_func_wrapper_with_typing,
    ):
        await stream_engine.start_streams()
        mock_func_wrapper_with_typing.assert_called()
        mock_consumer_start.assert_called()
        stream_cr_typing = stream_engine._streams[0]
        stream_all_typing = stream_engine._streams[1]

        assert stream_cr_typing == stream_one
        assert stream_all_typing == stream_two
        assert stream_cr_typing.topics == [topic]

        assert stream_cr_typing.udf_handler.type == UDFType.WITH_TYPING
        assert stream_all_typing.udf_handler.type == UDFType.WITH_TYPING


def test_add_stream_custom_conf(stream_engine: StreamEngine):
    topic = "dev-kpn-des--hello-kpn"

    @stream_engine.stream(
        topic,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    async def stream(_):
        pass

    with mock.patch.multiple(
        "kstreams.clients.Consumer", start=mock.DEFAULT, unsubscribe=mock.DEFAULT
    ), mock.patch("kstreams.clients.Producer.start") as mock_producer_start:
        stream_engine.sync_start()

        stream.consumer.start.assert_called()
        mock_producer_start.assert_called()

        assert stream.consumer._auto_offset_reset == "earliest"
        assert stream.consumer._group_id is None
        assert not stream.consumer._enable_auto_commit


def test_start_and_stop_engine(stream_engine: StreamEngine):
    @stream_engine.stream("dev-kpn-des--hello-kpn")
    async def stream(_):
        pass

    with mock.patch(
        "kstreams.clients.Consumer.start"
    ) as mock_consumer_start, mock.patch(
        "kstreams.clients.Producer.start"
    ) as mock_producer_start:
        stream_engine.sync_start()
        stream_engine.sync_stop()

    mock_consumer_start.assert_awaited_once()
    mock_producer_start.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_and_stop_streams(stream_engine: StreamEngine):
    @stream_engine.stream("dev-kpn-des--hello-kpn")
    async def stream(_):
        ...

    with mock.patch.multiple(
        "aiokafka.AIOKafkaConsumer", start=mock.DEFAULT, unsubscribe=mock.DEFAULT
    ):
        await stream_engine.start_streams()

        assert stream.running
        consumer = stream.consumer
        assert not consumer._closed

        await stream_engine.stop_streams()
        assert consumer._closed
        assert stream.consumer is None


@pytest.mark.asyncio
async def test_async_send_event(
    stream_engine: StreamEngine, record_metadata: RecordMetadata
):
    async def async_func():
        return record_metadata

    send = mock.AsyncMock(return_value=async_func())

    with mock.patch.multiple(
        aiokafka.AIOKafkaProducer, start=mock.DEFAULT, stop=mock.DEFAULT, send=send
    ):
        await stream_engine.start()
        metadata = await stream_engine.send(
            topic,
            value=value,
        )
        assert stream_engine._producer is not None
        assert metadata == record_metadata

        send.assert_awaited_with(
            topic,
            value=value,
            key=None,
            partition=None,
            timestamp_ms=None,
            headers=None,
        )
        await stream_engine.stop()


def test_sync_send_event(stream_engine: StreamEngine, record_metadata: RecordMetadata):
    async def async_func():
        return record_metadata

    send = mock.AsyncMock(return_value=async_func())

    with mock.patch.multiple(
        aiokafka.AIOKafkaProducer,
        start=mock.DEFAULT,
        stop=mock.DEFAULT,
        send=send,
    ):
        metadata = stream_engine.sync_send(
            topic,
            value=value,
            key="1",
        )

        assert metadata == record_metadata
        send.assert_awaited_once_with(
            topic,
            value=value,
            key="1",
            partition=None,
            timestamp_ms=None,
            headers=None,
        )


def test_sync_send_tombstone(
    stream_engine: StreamEngine, record_metadata: RecordMetadata
):
    async def async_func():
        return record_metadata

    send = mock.AsyncMock(return_value=async_func())

    with mock.patch.multiple(
        aiokafka.AIOKafkaProducer,
        start=mock.DEFAULT,
        stop=mock.DEFAULT,
        send=send,
    ):
        event_type = "hello.delete"
        headers = {"kpn-event-type": event_type}
        kafka_headers = [
            ("kpn-event-type", event_type.encode()),
        ]

        stream_engine.sync_send(topic, value=None, key=key, headers=headers)

        send.assert_called_once_with(
            topic,
            value=None,
            key=key,
            partition=None,
            timestamp_ms=None,
            headers=kafka_headers,
        )


def test_sync_send_custom_serializer(
    stream_engine: StreamEngine,
    record_metadata: RecordMetadata,
):
    stream_engine.serializer = MySerializer()

    async def async_func():
        return record_metadata

    send = mock.AsyncMock(return_value=async_func())

    with mock.patch.multiple(
        aiokafka.AIOKafkaProducer,
        start=mock.DEFAULT,
        stop=mock.DEFAULT,
        send=send,
    ):
        headers = {
            "schema-id": schema_id,
            "kpn-event-type": event_type,
            "content-type": consts.APPLICATION_JSON,
        }

        '{"message": "Hi KPN"}'

        metadata = stream_engine.sync_send(topic, value=value, key=key, headers=headers)
        assert metadata == record_metadata

        send.assert_called_once_with(
            topic,
            value=b'{"message": "Hi KPN"}',
            key=key,
            partition=None,
            timestamp_ms=None,
            headers=[
                ("schema-id", schema_id.encode()),
                ("kpn-event-type", event_type.encode()),
                ("content-type", consts.APPLICATION_JSON.encode()),
            ],
        )


@pytest.mark.asyncio
async def test_async_send_custom_serializer(
    stream_engine: StreamEngine, record_metadata: RecordMetadata
):
    stream_engine.serializer = MySerializer()

    async def async_func():
        return record_metadata

    send = mock.AsyncMock(return_value=async_func())

    with mock.patch.multiple(
        clients.Producer,
        start=mock.DEFAULT,
        stop=mock.DEFAULT,
        send=send,
    ):
        await stream_engine.start()
        metadata = await stream_engine.send(
            topic,
            value=value,
            headers={
                "schema-id": schema_id,
                "kpn-event-type": event_type,
                "content-type": consts.APPLICATION_JSON,
            },
        )

        assert metadata == record_metadata
        send.assert_awaited_with(
            topic,
            value=b'{"message": "Hi KPN"}',
            key=None,
            partition=None,
            timestamp_ms=None,
            headers=[
                ("schema-id", schema_id.encode()),
                ("kpn-event-type", event_type.encode()),
                ("content-type", consts.APPLICATION_JSON.encode()),
            ],
        )

        await stream_engine.stop()


@pytest.mark.asyncio
async def test_e2e_stream_old_fashion(stream_engine: StreamEngine):
    """
    Test the old fashion `async for in` loop to consume from stream
    """
    event = b'{"message": "Hello world!"}'

    # A mock to prove that the callback was called
    sync_to_db = mock.Mock()

    @stream_engine.stream(topic)
    async def my_stream(stream):
        async for cr in stream:
            assert cr.value == event
            sync_to_db(value)

    async with TestStreamClient(stream_engine=stream_engine) as client:
        await client.send(topic, value=event, key="1")

    sync_to_db.assert_called_once_with(value)


@pytest.mark.asyncio
async def test_e2e_cr_typing(stream_engine: StreamEngine):
    event = b'{"message": "Hello world!"}'

    # A mock to prove that the callback was called
    sync_to_db = mock.Mock()

    @stream_engine.stream(topic)
    async def my_stream(cr: ConsumerRecord):
        assert cr.value == event
        sync_to_db(value)

    async with TestStreamClient(stream_engine=stream_engine) as client:
        await client.send(topic, value=event, key="1")

    sync_to_db.assert_called_once_with(value)


@pytest.mark.asyncio
async def test_e2e_all_typing(stream_engine: StreamEngine):
    event = b'{"message": "Hello world!"}'

    # A mock to prove that the callback was called
    sync_to_db = mock.Mock()

    @stream_engine.stream(topic)
    async def my_stream(cr: ConsumerRecord, stream: Stream):
        assert cr.value == event
        sync_to_db(value)
        assert await stream.commit()

    async with TestStreamClient(stream_engine=stream_engine) as client:
        await client.send(topic, value=event, key="1")

    sync_to_db.assert_called_once_with(value)


@pytest.mark.asyncio
async def test_e2e_with_sync_send(stream_engine: StreamEngine):
    event = b'{"message": "Hello world!"}'

    # A mock to prove that the callback was called
    sync_to_db = mock.Mock()

    @stream_engine.stream(topic)
    async def my_stream(cr: ConsumerRecord):
        assert cr.value == event
        sync_to_db(event)

    async with TestStreamClient(stream_engine=stream_engine):
        # send event with StreamEngine rather than the client
        # this is a sync operation and kafka_python is used
        metadata = stream_engine.sync_send(topic, value=event, key="1")

        assert metadata.topic == topic
        assert metadata.partition == 0
        assert metadata.offset == 0

        metadata = stream_engine.sync_send(topic, value=event, key="1")
        assert metadata.topic == topic
        assert metadata.partition == 0
        assert metadata.offset == 1

    # the mock has been called twice because 2 events were produced
    sync_to_db.assert_has_calls([mock.call(event), mock.call(event)])


@pytest.mark.asyncio
async def test_e2e_with_sync_send_no_stream(stream_engine: StreamEngine):
    event = b'{"message": "Hello world!"}'

    def produce():
        # function to produce events. This function can be
        # a django view where an event is produced
        stream_engine.sync_send(topic, value=event, key="1")
        stream_engine.sync_send(topic, value=event, key="1")

    async with TestStreamClient(stream_engine=stream_engine) as client:
        produce()
        cr = await client.get_event(topic_name=topic)
        assert cr.value == event

        cr = await client.get_event(topic_name=topic)
        assert cr.value == event
