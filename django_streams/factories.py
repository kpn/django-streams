from typing import Optional, Type

from kstreams.backends.kafka import Kafka
from kstreams.clients import Consumer, Producer
from kstreams.prometheus.monitor import PrometheusMonitor
from kstreams.serializers import Deserializer, Serializer

from .engine import StreamEngine


def create_engine(
    *,
    title: Optional[str] = None,
    backend: Optional[Kafka] = None,
    consumer_class: Type[Consumer] = Consumer,
    producer_class: Type[Producer] = Producer,
    serializer: Optional[Serializer] = None,
    deserializer: Optional[Deserializer] = None,
    monitor: Optional[PrometheusMonitor] = None,
) -> StreamEngine:
    if monitor is None:
        monitor = PrometheusMonitor()

    if backend is None:
        backend = Kafka()

    return StreamEngine(
        title=title,
        backend=backend,
        consumer_class=consumer_class,
        producer_class=producer_class,
        serializer=serializer,
        deserializer=deserializer,
        monitor=monitor,
    )
