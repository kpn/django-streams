# Using the Django ORM

Django is a `synchronous` framework but as it was explained before, we can run `coroutines`. The coroutines can `await` other `coroutines`
and also call `sync` functions but they *CAN NOT* call the *django ORM* directly. If you have to call the *ORM*, you *MUST* use the `sync_to_async` adapter,
otherwise `django` will raise an error

```python
import logging
from asgiref.sync import sync_to_async
from kstreams import ConsumerRecord

from streaming.models import HelloWorld  # Your Model
from streaming.engine import stream_engine

logger = logging.getLogger(__name__)


@sync_to_async
def get_object():
    return HelloWorld.objects.get_or_create(pk=1)


@sync_to_async
def increase(my_object):
    my_object.total += 1
    my_object.save()

    logger.info(f"Total increased to {my_object.total}")



@stream_engine.stream("dev-des--hello-kpn", group_id="my-group-id")
async def consumer_task(cr: ConsumerRecord)::
    logger.info(f"Event consumed: headers: {cr.headers}, payload: {cr.value}")
    
    my_object, _ = await get_object()
    await increase(my_object)
```

!!! note
    The package `asgiref` is required in order to use `sync_to_async` or `async_to_sync`. Use `poetry add asgiref`
