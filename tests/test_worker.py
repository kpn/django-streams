from unittest import mock

from django.core.management import call_command

from django_streams.engine import StreamEngine


def test_worker(stream_engine: StreamEngine):
    topic = "dev-kpn-des--hello-kpn"

    # Add a stream
    @stream_engine.stream(topic)
    async def stream(_):
        pass

    stream_instance = stream_engine._streams[0]
    assert stream_instance == stream
    assert stream_instance.topics == [topic]
    assert not stream_instance.running

    with mock.patch("kstreams.clients.Consumer.start"), mock.patch(
        "kstreams.clients.Producer.start"
    ):
        call_command("worker")
        assert stream_engine.loop
        assert stream_instance.running
