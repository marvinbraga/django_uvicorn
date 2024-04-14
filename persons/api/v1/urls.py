from django.urls import include, path
from rest_framework.routers import DefaultRouter

from persons.api.v1 import views
from persons.api.v1.views import CheckPersonAPIView, CreatePersonAPIView, AsyncCreatePersonAPIView

router = DefaultRouter()
router.register(r'persons', views.PersonViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('check/', CheckPersonAPIView.as_view(), name='check'),
    path('create_bulk/', CreatePersonAPIView.as_view(), name='create-bulk'),
    path('fetch_data/', AsyncCreatePersonAPIView.as_view(), name='fetch-data'),
]
