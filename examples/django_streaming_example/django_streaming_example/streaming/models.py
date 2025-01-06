from django.db import models


class HelloWorld(models.Model):
    total = models.PositiveIntegerField(default=0)
