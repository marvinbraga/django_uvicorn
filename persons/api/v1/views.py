from rest_framework import viewsets

from persons.api.v1.serializers import PersonSerializer
from persons.models import Person


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
