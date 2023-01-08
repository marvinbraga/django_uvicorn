from django.urls import path, include
from persons.api.v1 import urls as urls_v1
urlpatterns = [
    path('api/v1/', include(urls_v1)),
]
