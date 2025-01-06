# Producing events

Produce events in your `django` applications is quite straightforward. It can be done in an `async` or `sync` context.

- In a `sync` context for example in a `django view` or a `background task` you must use the `sync_send` method.
- In an `async` context, for example in a `kafka consumer` you must use the `send` method.

## Producing in a sync context

The following example shows the simplest and probably common use case: producing an event in a `django view`:

```python
# streaming_app/views.py
from django.http import HttpResponse
from django.views.generic import View

from de.core.conf import settings
from .engine import stream_engine


class HelloWorldView(View):
    def get(self, request, *args, **kwargs):
        topic = f"{settings.KAFKA_TOPIC_PREFIX}hello-kpn"

        record_metadata = stream_engine.sync_send(
            topic,
            value=b"hello world!!!",
            key="hello",
            partition=None,
            timestamp_ms=None,
            headers=None,
        )

        return HttpResponse(f"Event metadata: {record_metadata}")
```

!!! note
    The engine must be created in order to use the `sync_send` function

!!! note
    Any extra metadata for example `Content Type` can be specified using the header `content-type`

!!! note
    The returned value after producing is `RecordMetadata`

## Producing in an async context

Producing events in an `async` context, for example inside a coroutine must be done using `await engine.send(...)`

```python
from kstreams import ConsumerRecord

from .engine import stream_engine


hello_world_topic = "dev-kpn-des--hello-kpn"
hello_world_two_topic = "dev-kpn-des--hello-kpn-2"

@stream_engine.stream(hello_world_topic, group_id="django-streaming-example-group-id")
async def consumer_task(cr: ConsumerRecord):
    logger.info(f"Event consumed: headers: {headers}, payload: {payload}")

    await stream_engine.send(
        hello_world_two_topic,
        value=b"hello world!!!,
        key="hello",
    )
```

!!! note:
    Do not use the function `stream_engine.sync_send(...)` inside a coroutine because it is blocking!!
