from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("accounts.urls", namespace="accounts")),
    # path("", include("dashboard.urls", namespace="dashboard")),
    path("", include("contributions.urls", namespace="contributions")),
]

urlpatterns += [path('i18n/', include('django.conf.urls.i18n')),]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
