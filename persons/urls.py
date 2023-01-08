from django.urls import path, include

urlpatterns = [
    path('', include('persons.api.urls')),
]
