from django.urls import path

from .views import HelloWorldView, ProduceTombStone, StressTestView

urlpatterns = [
    path("produce/hello-world/", HelloWorldView.as_view()),
    path("produce/tombstone/", ProduceTombStone.as_view()),
    path("produce/hello-world/<int:total_events>/", StressTestView.as_view()),
]
