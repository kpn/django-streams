from django.apps import AppConfig


class StreamingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_streaming_example.streaming"

    def ready(self):
        from . import streams  # noqa F401
