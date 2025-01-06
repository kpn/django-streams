# Test Client

To test your `streams` or perform `e2e` tests you can make use of the `test_utils.TestStreamClient`.
The `TestStreamClient` you can send events so you won't need a `producer`

Let's assume that you have the following code example:

```python
# streams.py
from kstreams import ConsumerRecord

from .engine import stream_engine


topic = "dev-kpn-des--kstreams"

def save_to_db(value):
    # Store the value in your Database
    ...


@stream_engine.stream(topic, group_id="example-group")
async def consume(cr: ConsumerRecord):
    print(f"Event consumed: headers: {cr.headers}, payload: {cr.value}")
    save_to_db(value)
```

In order to test it, you could mock the kafka `Consumer` and `Producer` or use the `TestStreamClient`

```python
# test_stream.py
import pytest
from django_streams.test_utils import TestStreamClient

from .engine import stream_engine


@pytest.mark.asyncio
async def test_streams_consume_events():
    topic = "dev-kpn-des--kstreams"  # Use the same topic as the stream
    event = b'{"message": "Hello world!"}'

    with patch("example.on_consume") as save_to_db:
        async with TestStreamClient(stream_engine=stream_engine) as test_client:
            metadata = await test_client.send(topic, value=event, key="1")  # send the event with the test client
            current_offset = metadata.offset
            assert metadata.topic == topic

            # send another event and check that the offset was incremented
            metadata = await test_client.send(topic, value=b'{"message": "Hello world!"}', key="1")
            assert metadata.offset == current_offset + 1

    # check that the event was consumed
    assert save_to_db.called
```

## Sync Producer only

In some scenarios, your application will only produce events in a `synchronous` way and other application/s will consume it, but you want to make sure that
the event was procuced in a proper way and the `topic` contains that `event`.

```python
# producer_example.py
from .engine import stream_engine


topic = "dev-kpn-des--hello-world"


def produce(event):
    # function to produce events. This function can be
    # a django view where an event is produced
    stream_engine.sync_send(topic, value=event, key="1")
```

Then you could have a test_producer_example.py file to test the code:

```python
from producer_example import topic, produce


@pytest.mark.asyncio
async def test_e2e_with_sync_producer_no_stream(stream_engine: StreamEngine):
    event = b'{"message": "Hello world!"}'

    async with TestStreamClient(stream_engine=stream_engine) as client:
        # produce 2 events
        produce(event)
        produce(event)
        
        # check that the event was placed in a topic in a proper way
        consumer_record = await client.get_event(topic_name=topic)
        assert consumer_record.value == event

        # check that the event was placed in a topic in a proper way
        consumer_record = await client.get_event(topic_name=topic)
        assert consumer_record.value == event
```
