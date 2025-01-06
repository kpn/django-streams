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
