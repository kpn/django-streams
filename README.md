# Django application to produce/consume events from Kafka

![django streaming](docs/img/django_worker.png)

![Build status](https://github.com/kpn/django-streams/actions/workflows/pr-tests.yaml/badge.svg?branch=main)
[![codecov](https://codecov.io/gh/kpn/django-streams/branch/main/graph/badge.svg?token=t7pxIPtphF)](https://codecov.io/gh/kpn/django-streams)
![python version](https://img.shields.io/badge/python-3.9%2B-yellowgreen)

## Installation

```bash
pip install django-streams
```

or with poetry

```bash
poetry add django-streams
```

and add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_streams",
    ...
    "my_streams_app",
    # etc...
]
```

## Documentation

https://kpn.github.io/django-streams/

## Usage

create the `engine`:

```python
# my_streams_app/engine.py
from django_streams import create_engine

from kstreams.backends import Kafka


stream_engine = create_engine(
    title="test-engine",
    backend=Kafka(),
)
```

*To configure the backend follow the [kstreams backend documentation](https://kpn.github.io/kstreams/backends/)*

### Consuming events

Define your streams:

```python
# my_streams_app/streams.py
from kstreams import ConsumerRecord
from .engine import stream_engine


@stream_engine.stream("dev-kpn-des--hello-kpn", group_id="django-streams-principal-group-id")  # your consumer
async def consumer_task(cr: ConsumerRecord):
    async for cr in stream:
        logger.info(f"Event consumed: headers: {cr.headers}, value: {cr.value}")
```

and then in your `apps.py` you must import the `python module` or your `coroutines`

```python
# my_streams_app/apps.py
from django.apps import AppConfig


class StreamingAppConfig(AppConfig):
    name = "streaming_app"

    def ready(self):
        from . import streams  # import the streams module
```

Now you can run the worker:

```bash
python manage.py worker
```

### Producing events

Producing events can be `sync` or `async`. If you are in a `sync` context you must use `stream_engine.sync_send`, otherwise [stream_engine.send](https://pages.kpn.org/repos-docs/dsl/django-streams/producer/#producing-in-an-async-context). For both cases a `RecordMetadata` is returned.

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
            value=b"hello world",
            key="hello",
            partition=None,
            timestamp_ms=None,
            headers=None,
        )

        return HttpResponse(f"Event metadata: {record_metadata}")
```

## Benchmark

Producer:

| Total produced events | Time (seconds) |
|--------------|----------------|
| 1 | 0.004278898239135742 |
| 10 | 0.030963897705078125 |
| 100 | 0.07049298286437988 |
| 1000 | 0.6609988212585449 |
| 10000 | 6.501222133636475 |

## Running tests

```bash
./scrtips/test
```

## Code formating

```bash
./scrtips/format
```
