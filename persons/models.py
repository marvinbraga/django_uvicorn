from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.age})"
