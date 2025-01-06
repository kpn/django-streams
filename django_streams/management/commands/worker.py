import logging
import signal

from django.core.management.base import BaseCommand

from django_streams.factories import create_engine

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start Worker to consume from kafka topics"

    def handle(self, *args, **options):
        # StreamEngine is a Singlenton, so it will return the same instance
        # as the user has defined in the custom django app.
        engine = create_engine()
        logger.info(f"Starting worker with engine {engine}")

        # Listening signals from main Thread
        signal.signal(signal.SIGINT, engine.sync_stop)
        signal.signal(signal.SIGTERM, engine.sync_stop)

        # start app
        engine.sync_start()
