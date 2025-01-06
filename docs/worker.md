# How the worker runs?

`django-streams` has a custom command to run the worker that will take of running the `streams` and manage the `gracefully shutdown`.

```bash
python manage.py worker
```

The custom `django command` does two things:

1. Subscribe to `signal.SIGINT` and `signal.SIGTERM` to stop the worker
2. Start the `engine`

```python
# django_streams.management.commands.worker.py
import logging
import signal

from django.core.management.base import BaseCommand

from django_streams.factories import create_engine

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start kafka consumers"

    def handle(self, *args, **options):
        # StreamEngine is a Singlenton, so it will return the same instance
        # as the user has defined in the custom django app.
        engine = create_engine()
        logger.info(f"Starting Engine with streams {engine._streams}")

        # Listening signals from main Thread
        signal.signal(signal.SIGINT, engine.sync_stop)  # IMPORTANT
        signal.signal(signal.SIGTERM, engine.sync_stop) # IMPORTANT

        # start worker
        engine.sync_start()
```

## Signals

When you write a custom command in `django` you are in a `sync` context but `coroutines` must run in an `async` context.

When the `command/program` finishes, the `main thread` finishes but not the `secondary thread`, unless that the worker is subscribed to
the signals `signal.SIGINT` and `signal.SIGTERM`. Subscribing to the signals will guarantee that:

1. The `kafka consumers` are stopped in a proper way.
2. Gracefully shutdown.
3. If you are using `kubernetes`, the pod will be terminated faster.

So, the `worker` *have* to subscribe to the signals:

```python
def handle(self, *args, **options):
    # Listening signals from main Thread
    signal.signal(signal.SIGINT, engine.sync_stop)  # IMPORTANT
    signal.signal(signal.SIGTERM, engine.sync_stop) # IMPORTANT

    # start the engine
    engine.sync_start()
```
