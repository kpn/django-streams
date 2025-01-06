import time

from django.http import HttpResponse
from django.views.generic import View
from kstreams import consts

from .engine import stream_engine
from .utils import hello_topic


class HelloWorldView(View):
    def get(self, _, *args, **kwargs):
        record_metadata = stream_engine.sync_send(
            hello_topic,
            value={"message": f"hello world topic {hello_topic}"},
            headers={
                "kpn-event-type": "hello_world.test",
                "content-type": consts.APPLICATION_JSON,
            },
            key="hello",
            partition=None,
            timestamp_ms=None,
        )

        return HttpResponse(
            f"Event produced to topic {hello_topic} with RecordMetadata {record_metadata}"
        )


class ProduceTombStone(View):
    def get(self, _, *args, **kwargs):
        record_metadata = stream_engine.sync_send(
            hello_topic,
            value=None,
            headers={
                "kpn-event-type": "hello_world.test",
            },
            key="hello",
            partition=None,
            timestamp_ms=None,
        )

        return HttpResponse(
            f"Event produced to topic {hello_topic} with RecordMetadata {record_metadata}"
        )


class StressTestView(View):
    def get(self, _, total_events, *args, **kwargs):
        counter = 0
        start_time = time.time()
        while counter < total_events:
            stream_engine.sync_send(
                hello_topic,
                value={"message": f"hello world topic {hello_topic}"},
                headers={
                    "kpn-event-type": "hello_world.test",
                    "content-type": consts.APPLICATION_JSON,
                },
                key="hello",
                partition=None,
                timestamp_ms=None,
            )

            counter += 1
        return HttpResponse(
            f"{counter} event produced to topic {hello_topic} in {time.time() - start_time} seconds"
        )
