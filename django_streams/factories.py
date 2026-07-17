from typing import Optional, Type

from kstreams.backends.kafka import Kafka
from kstreams.clients import Consumer, Producer, ProducerSettings
from kstreams.prometheus.monitor import PrometheusMonitor
from kstreams.serializers import Deserializer, Serializer
from kstreams.types import EngineHooks

from .engine import StreamEngine


def create_engine(
    *,
    title: Optional[str] = None,
    backend: Optional[Kafka] = None,
    consumer_class: Type[Consumer] = Consumer,
    producer_class: Type[Producer] = Producer,
    producer_settings: Optional[ProducerSettings] = None,
    serializer: Optional[Serializer] = None,
    deserializer: Optional[Deserializer] = None,
    monitor: Optional[PrometheusMonitor] = None,
    on_startup: Optional[EngineHooks] = None,
    on_stop: Optional[EngineHooks] = None,
    after_startup: Optional[EngineHooks] = None,
    after_stop: Optional[EngineHooks] = None,
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
        producer_settings=producer_settings,
        serializer=serializer,
        deserializer=deserializer,
        monitor=monitor,
        on_startup=on_startup,
        on_stop=on_stop,
        after_startup=after_startup,
        after_stop=after_stop,
    )
