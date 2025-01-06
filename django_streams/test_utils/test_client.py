from datetime import datetime
from typing import Any, Dict, Optional

from aiokafka.structs import RecordMetadata, TopicPartition
from kstreams import ConsumerRecord, types
from kstreams.test_utils import TestStreamClient as Base
from kstreams.test_utils import TopicManager

from django_streams.engine import Base as BaseEngine
from django_streams.engine import StreamEngine


class TestStreamClient(Base):
    __test__ = False

    def __init__(self, *args, **kwargs) -> None:
        """
        Redifine the __init__ method because py_streams.test_utils.TestStreamClient
        will use a py_streams.StreamEngine but we want a django_streams.StreamEngine
        """
        super().__init__(*args, **kwargs)

        # monkey patch get_sync_producer to make sure that a kafka connection never happens
        StreamEngine.sync_send = self.sync_send  # type: ignore

        # monkey patch the start_streams as the django_streams engine runs them not in an asyncio.Task
        StreamEngine.start_streams = BaseEngine.start_streams  # type: ignore

    def sync_send(
        self,
        topic_name: str,
        *,
        value: Optional[Dict] = None,
        key: Optional[Any] = None,
        partition: int = 0,
        timestamp_ms: Optional[int] = None,
        headers: Optional[types.EncodedHeaders] = None,
        **kwargs,
    ) -> RecordMetadata:
        """
        Method intended to monkey patch the stream_engine.sync_send method
        in order to make sure that the TestClient does not connect to kafka.
        """
        topic, created = TopicManager.get_or_create(topic_name)
        timestamp_ms = timestamp_ms or int(round(datetime.now().timestamp()))
        partition = partition or 0
        total_partition_events = topic.offset(partition=partition)
        offset = total_partition_events + 1

        consumer_record: ConsumerRecord = ConsumerRecord(
            topic=topic_name,
            value=value,
            key=key,
            headers=headers or [],
            partition=partition,
            timestamp=timestamp_ms,
            offset=offset,
            timestamp_type=0,
            checksum=None,
            serialized_key_size=-1 if key is None else len(key),
            serialized_value_size=-1 if value is None else len(value),
        )

        # put the ConsumerRecord in the asyncio.Queue so it can be consumed by the streams
        topic.put_nowait(event=consumer_record)

        return RecordMetadata(
            topic=topic_name,
            partition=partition,
            timestamp=timestamp_ms,
            offset=offset,
            topic_partition=TopicPartition(topic=topic_name, partition=partition),
            timestamp_type=0,
            log_start_offset=None,
        )
