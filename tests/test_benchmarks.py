"""
This file contians benchmarks for django-kstreams.

Interpreting the data:

- Name: Name of the test or function being benchmarked.
- Min: The shortest execution time recorded across all runs.
- Max: The longest execution time recorded.
- Mean: The average execution time across all runs.
- StdDev: The standard deviation of execution times, representing the variability of the
    measurements. A low value indicates consistent performance.
- Median: The middle value when all execution times are sorted.
- IQR (Interquartile Range): The range between the 25th and 75th percentile of execution
    times. It’s a robust measure of variability that’s less sensitive to outliers.
- Outliers: Measurements that significantly differ from others.
    E.g., 5;43 means 5 mild and 43 extreme outliers.
- OPS (Operations Per Second): How many times the function could be executed
    in one second (calculated as 1 / Mean).
- Rounds: The number of times the test was run.
- Iterations: Number of iterations per round.

Performance may be affected by:
- Power-saving modes
- CPU frequency scaling
- Background Processes

To get accurate results, run benchmarks on a dedicated machine with no other
applications running.

The result unit varies depending on the benchmark duration:

- s: seconds
- ms: milliseconds = 1,0 x 10-3 seconds
- us: microseconds = 1,0 x 10-6 seconds
- ns: nanoseconds = 1,0 x 10-9 seconds

## Profiling

Profile and visualize your code with `py-spy`:

```python
pip install py-spy
sudo py-spy record -o profile.svg -- python tests/test_benchmarks.py
```

"""

from unittest import mock

import aiokafka
from kstreams.test_utils.structs import RecordMetadata

from django_streams.engine import StreamEngine

topic = "dev-kpn-des--hello-world"
value = {"message": "Hi KPN"}
event_type = "hello_world.test"
schema_id = "example/hello_kpn/v0.0.1/schema.avsc"
key = "hello"


def bench_sync_send(stream_engine: StreamEngine, record_metadata: RecordMetadata):
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


def test_sync_send(
    benchmark,
    stream_engine: StreamEngine,
    record_metadata: RecordMetadata,
):
    # benchmark something
    benchmark(bench_sync_send, stream_engine, record_metadata)
