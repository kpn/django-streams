import http

import pytest
from django_streaming_example.streaming.views import hello_topic


@pytest.mark.asyncio
async def test_produce_hello_world(client, stream_client):
    async with stream_client:
        resp = client.get("/streaming/produce/hello-world/")
        assert resp.status_code == http.HTTPStatus.OK
        consumer_record = await stream_client.get_event(topic_name=hello_topic)
        assert consumer_record.value == {"message": f"hello world topic {hello_topic}"}


@pytest.mark.asyncio
async def test_tombstone(client, stream_client):
    async with stream_client:
        resp = client.get("/streaming/produce/tombstone/")
        assert resp.status_code == http.HTTPStatus.OK
        consumer_record = await stream_client.get_event(topic_name=hello_topic)
        assert not consumer_record.value
