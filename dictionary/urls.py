from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminRootViewSet, AdminWordViewSet, WordViewSet

public_router = DefaultRouter()
public_router.register(r"words", WordViewSet, basename="word")

admin_router = DefaultRouter()
admin_router.register(r"words", AdminWordViewSet, basename="admin-word")
admin_router.register(r"roots", AdminRootViewSet, basename="admin-root")

urlpatterns = public_router.urls + [
    path("admin/", include(admin_router.urls)),
]
