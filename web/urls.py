from django.urls import path

from .views import MTPicksAppView

urlpatterns = [
    path("", MTPicksAppView.as_view(), name="mtpicks-home"),
]
