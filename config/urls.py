from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("racing.urls")),
    path("api/integrations/", include("integrations.urls")),
    path("api/referrals/", include("referrals.urls")),
]
