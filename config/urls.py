from django.contrib import admin
from django.urls import include, path

# Spanish branding + dashboard stats (overrides AdminSite.index)
import config.admin  # noqa: F401

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("racing.urls")),
    path("api/integrations/", include("integrations.urls")),
    path("api/referrals/", include("referrals.urls")),
    path("", include("web.urls")),
]
