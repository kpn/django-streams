import asyncio

import pytest
from django_streaming_example.streaming.streams import (
    hello_topic,
    hello_topic_enriched,
    stream_engine,
)
from kstreams import consts

from django_streams.test_utils.test_client import TestStreamClient


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_streams_e2e():
    """
    Test the stream End2End.

    Produce an event and check that the stream consume it and then
    store the object in the DB.

    @pytest.mark.django_db should be use in order to have a `transactional_db`
    """
    async with TestStreamClient(
        stream_engine=stream_engine, topics=[hello_topic_enriched]
    ) as client:
        await client.send(
            hello_topic,
            key="hello",
            value={"message": f"hello world topic {hello_topic}"},
            headers={
                "kpn-event-type": "hello_world.test",
                "content-type": consts.APPLICATION_JSON,
            },
        )

        # Let's check if it was received by the target topic
        await asyncio.sleep(2)
        assert await client.get_event(topic_name=hello_topic_enriched)
