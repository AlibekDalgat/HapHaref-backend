"""Root URL configuration for the HapHaref backend."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "HapHaref — администрирование словаря"
admin.site.site_title = "HapHaref admin"
admin.site.index_title = "Управление старотатарским словарём"

admin.site.has_permission = lambda request: bool(
    getattr(request.user, "is_active", False)
    and getattr(request.user, "is_superuser", False)
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("dictionary.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
