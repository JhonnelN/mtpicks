from django.views.generic import TemplateView


class MTPicksAppView(TemplateView):
    """Public MTPicks web frontend (splash + app shell)."""

    template_name = "web/index.html"
