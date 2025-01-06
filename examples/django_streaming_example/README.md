# django-streaming-example

## Installation

```bash
poetry install
```

Activate virtual environment

```bash
poetry shell
```

## Run the application

Launch `kafka` cluster

```bash
make kafka-kluster
```

and in another terminal:

```bash
make dev-topics
```

Then lunch `Django` development server

```bash
make migrate
make devserver
```

To run the worker to consume kafka events run:

```bash
make worker
```

This will ensure your application is running in a container, with hot code reload enabled.

## Streaming

Streaming capabilities are provided by [django-streams](https://kpn.github.io/django-streams/).

## Usage

In order to consume events from `kafka topics` you have to define your engine and streams. The `streaming.streams` module contains all you need to start consuming. Example:

```python
# streaming.engine
import ssl
from typing import Optional

from django.conf import settings

from kstreams import utils
from kstreams.backends import kafka

from django_streams import create_engine

from .serializer import JsonSerializer


def get_ssl_context() -> Optional[ssl.SSLContext]:
    if settings.KAFKA_CONFIG_SECURITY_PROTOCOL != kafka.SecurityProtocol.SSL:
        return None

    return utils.create_ssl_context_from_mem(
        certdata=settings.KAFKA_SSL_CERT_DATA,
        keydata=settings.KAFKA_SSL_KEY_DATA,
        cadata=getattr(settings, "KAFKA_SSL_CABUNDLE_DATA", None),
    )


backend = kafka.Kafka(
    bootstrap_servers=settings.KAFKA_CONFIG_BOOTSTRAP_SERVERS,
    security_protocol=settings.KAFKA_CONFIG_SECURITY_PROTOCOL,
    ssl_context=get_ssl_context(),
)

stream_engine = create_engine(
    title="test-engine",
    backend=backend,
    serializer=JsonSerializer(),
)
```

Then define your `streams`

```python
# streaming.streams
from kstreams import ConsumerRecord, middleware

from .middleware import JsonDeserializerMiddleware
from .engine import parser, stream_engine
from .utils import hello_topic


@stream_engine.stream(
    hello_topic,
    group_id="django-streams-example-hello-kpn",
    middlewares=[middleware.Middleware(JsonDeserializerMiddleware)],
)
async def consumer_task(cr: ConsumerRecord):
    logger.info(f"Event consumed: headers: {cr.headers}, payload: {cr.value} \n")
    ...
```

Producing events is also straightforward, example:

```python
# streaming.views
from django.http import HttpResponse
from django.views.generic import View
from kstreams import consts

from .engine import stream_engine
from .utils import hello_topic, successed_produce_callback


class HelloWorldView(View):
    def get(self, _, *args, **kwargs):
        future_metadata = stream_engine.sync_send(
            hello_topic,
            value={"message": f"hello world topic {hello_topic}"},
            headers={
                "event-type": "hello_world.test",
                "content-type": "application/json",
            },
            key="hello",
            partition=None,
            timestamp_ms=None,
        )

        future_metadata.add_callback(successed_produce_callback)
        return HttpResponse(f"Event produced to topic {hello_topic}")
```

## Useful Commands

|Command|Description| Default values|Example|
|-------|------------|--------------|-------|
| `make kafka-cluster`      | Run the kafka cluster          |      ---        | |
| `make stop-kafka-cluster`      |  Stop kafka cluster and clean containers         |     ---         | |
| `make list-topics`      |      List topics     |    ---          | |
| `make create-topic replication-factor={replication-factor} --partitions={number-of-partitions} topic-name={your-topic-name}`      |  Create topic         |  replication-factor=1 partitions=1           |  `make create-topic topic-name=test-topic`|

## Application example

- Go to `/streaming/produce/hello-world/` to produce an event to `hello-kpn` topic.
- Another `container` is running which consumes events from the topic `hello-kpn`. The container `command` is `make worker` which is doing `python manage.py worker`. The worker will
  run all the streams of you application. You can find the `streams` [here](https://git.kpn.org/projects/DE/repos/django-streaming-example/browse/src/django_streaming_example/streaming/streams.py?at=refs%2Fheads%2Ffix%2Fupdate-project-with-latest-template-changes)
- The worker runs in a different [k8s deployment](https://git.kpn.org/projects/DE/repos/django-streaming-example/browse/k8s/templates/worker.yaml) than the application (django), so kafka consumers can be scaled in/out independently.
- If you want to produce a `tombstone` then hit the endpoint `/streaming/produce/tombstone/`
