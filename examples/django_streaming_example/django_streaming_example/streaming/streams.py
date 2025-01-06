import logging

from asgiref.sync import sync_to_async
from kstreams import ConsumerRecord, consts, middleware

from .engine import stream_engine
from .middleware import JsonDeserializerMiddleware
from .models import HelloWorld
from .utils import hello_topic, hello_topic_enriched

logger = logging.getLogger(__name__)


@sync_to_async
def get_object(pk: int = 1):
    instance, _ = HelloWorld.objects.get_or_create(pk=pk)
    return instance


@sync_to_async
def save_to_db(instance):
    instance.total += 1
    instance.save()
    logger.info(f"Total increased to {instance.total}")


@stream_engine.stream(
    hello_topic,
    group_id="django-streams-example-hello-kpn",
    middlewares=[middleware.Middleware(JsonDeserializerMiddleware)],
)
async def consumer_task(cr: ConsumerRecord):
    logger.info(f"Event consumed: headers: {cr.headers}, payload: {cr.value} \n")
    metadata = await stream_engine.send(
        hello_topic_enriched,
        value={"message": f"hello world topic {hello_topic_enriched}"},
        headers={
            "kpn-event-type": "hello_world.test",
            "content-type": consts.APPLICATION_JSON,
        },
        key="hello",
    )

    logger.info(f"Event produced with metadata {metadata} \n")
    instance = await get_object()
    await save_to_db(instance)
