from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("accounts_app.api.urls")),
    path("api/", include("offers_app.api.urls")),
    path("api/", include("orders_app.api.urls")),
    path("api/", include("reviews_app.api.urls")),
    path("api/", include("base_info_app.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
