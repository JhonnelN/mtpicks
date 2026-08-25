"""
Django settings for American Horse Racing VIP Picker API.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Prefer .env over stale shell exports (important for tunnel hosts)
load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-in-production",
)

DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "django_filters",
    "corsheaders",
    "django_crontab",
    # Local apps
    "racing.apps.RacingConfig",
    "scraper",
    "integrations.apps.IntegrationsConfig",
    "referrals.apps.ReferralsConfig",
    "web.apps.WebConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
# US East Coast is the primary racing timezone for this product
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Jazzmin admin UI (Spanish)
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "VIP Picker Admin",
    "site_header": "American Horse Racing VIP Picker",
    "site_brand": "VIP Picker",
    "welcome_sign": "Bienvenido al panel de administración",
    "copyright": "American Horse Racing VIP Picker",
    "search_model": ["racing.Track", "racing.Race", "referrals.ReferralProfile"],
    "topmenu_links": [
        {"name": "Inicio", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/health/", "new_window": True},
        {"name": "Our Picks CNL", "url": "/api/our-picks/?track=CNL", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "order_with_respect_to": [
        "racing",
        "racing.Track",
        "racing.RaceDay",
        "racing.Race",
        "racing.RaceResult",
        "racing.RaceTipSheet",
        "racing.VipPick",
        "racing.OddsSnapshot",
        "racing.OddsMovement",
        "racing.ScrapeJob",
        "integrations",
        "referrals",
        "auth",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "racing.Track": "fas fa-flag-checkered",
        "racing.RaceDay": "fas fa-calendar-day",
        "racing.Race": "fas fa-horse",
        "racing.RaceResult": "fas fa-trophy",
        "racing.RaceTipSheet": "fas fa-lightbulb",
        "racing.VipPick": "fas fa-gem",
        "racing.OddsSnapshot": "fas fa-chart-line",
        "racing.OddsMovement": "fas fa-exchange-alt",
        "racing.ScrapeJob": "fas fa-robot",
        "racing.Runner": "fas fa-shoe-prints",
        "racing.Payout": "fas fa-dollar-sign",
        "integrations.WebhookEndpoint": "fas fa-plug",
        "integrations.WebhookDelivery": "fas fa-paper-plane",
        "referrals.ReferralProfile": "fas fa-share-alt",
        "referrals.ReferralAttribution": "fas fa-user-friends",
        "referrals.RewardLedger": "fas fa-coins",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "admin/css/vip_admin.css",
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-warning",
    "navbar": "navbar-dark navbar-primary",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "default_theme_mode": "light",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Required for admin login behind HTTPS tunnels (ngrok / Cloudflare)
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# ---------------------------------------------------------------------------
# Scraper configuration
# ---------------------------------------------------------------------------
# Single source or comma-separated failover chain, e.g.:
# equibase,racing_api,demo
SCRAPER_SOURCE = os.getenv("SCRAPER_SOURCE", "equibase,racing_api,demo")
SCRAPER_SOURCES = [
    s.strip().lower()
    for s in SCRAPER_SOURCE.split(",")
    if s.strip()
] or ["demo"]
SCRAPER_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (compatible; AHRVIPPicker/1.0; +https://localhost)",
)
SCRAPER_REQUEST_DELAY_SECONDS = float(os.getenv("SCRAPER_REQUEST_DELAY_SECONDS", "1.5"))
SCRAPER_TIMEOUT_SECONDS = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "30"))

# Optional licensed data provider (The Racing API - North America add-on)
RACING_API_USERNAME = os.getenv("RACING_API_USERNAME", "")
RACING_API_PASSWORD = os.getenv("RACING_API_PASSWORD", "")
RACING_API_BASE_URL = os.getenv("RACING_API_BASE_URL", "https://api.theracingapi.com")

# Optional Goalserve horse racing feed
GOALSERVE_API_KEY = os.getenv("GOALSERVE_API_KEY", "")
GOALSERVE_BASE_URL = os.getenv(
    "GOALSERVE_BASE_URL", "http://www.goalserve.com/getfeed"
)

# Primary US thoroughbred tracks for VIP product coverage
DEFAULT_TRACK_CODES = [
    code.strip().upper()
    for code in os.getenv(
        "DEFAULT_TRACK_CODES",
        "GP,CD,SAR,BAQ,AQU,BEL,SA,DMR,KEE,OP,PIM,LRL,IND,ELP,FG,TAM,TP,WO",
    ).split(",")
    if code.strip()
]

# Cron jobs (America/New_York). Requires: python manage.py crontab add
# Format: minute hour day month day_of_week
CRONJOBS = [
    # Morning entries for today + tomorrow (before first post)
    ("15 6 * * *", "scraper.cron.scrape_entries_job"),
    # Late morning refresh for scratches / program changes
    ("0 10 * * *", "scraper.cron.scrape_entries_job"),
    # Live status + results during race day windows (every 5 min, 11:00-23:55 ET)
    ("*/5 11-23 * * *", "scraper.cron.scrape_live_job"),
    # Denser near-post scrape (odds @ 5 MTP) every 2 minutes in race window
    ("*/2 11-23 * * *", "scraper.cron.scrape_near_post_job"),
    # Full results catch-up after the card
    ("30 23 * * *", "scraper.cron.scrape_results_job"),
    # Weekly track calendar sync (Sunday night)
    ("0 1 * * 0", "scraper.cron.sync_tracks_job"),
]

CRONTAB_LOCK_JOBS = True

# ---------------------------------------------------------------------------
# Integrations: webhooks + Telegram VIP channel
# ---------------------------------------------------------------------------
INTEGRATIONS_ADMIN_TOKEN = os.getenv("INTEGRATIONS_ADMIN_TOKEN", "dev-admin-token")
WEBHOOK_TIMEOUT_SECONDS = int(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "10"))
WEBHOOK_MAX_ATTEMPTS = int(os.getenv("WEBHOOK_MAX_ATTEMPTS", "3"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_VIP_CHAT_ID = os.getenv("TELEGRAM_VIP_CHAT_ID", "")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Referrals / rewards
# ---------------------------------------------------------------------------
REFERRAL_SHARE_BASE_URL = os.getenv(
    "REFERRAL_SHARE_BASE_URL", "https://vip.example.com/r/{code}"
)
REFERRAL_REWARD_REFERRER_CREDITS = int(os.getenv("REFERRAL_REWARD_REFERRER_CREDITS", "10"))
REFERRAL_REWARD_REFERRER_VIP_DAYS = int(os.getenv("REFERRAL_REWARD_REFERRER_VIP_DAYS", "1"))
REFERRAL_REWARD_REFEREE_CREDITS = int(os.getenv("REFERRAL_REWARD_REFEREE_CREDITS", "5"))
REFERRAL_MAX_REWARDS_PER_DAY = int(os.getenv("REFERRAL_MAX_REWARDS_PER_DAY", "20"))

# Near-post window for denser odds capture
NEAR_POST_MTP_THRESHOLD = int(os.getenv("NEAR_POST_MTP_THRESHOLD", "15"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "scraper": {"handlers": ["console"], "level": "INFO"},
        "racing": {"handlers": ["console"], "level": "INFO"},
        "integrations": {"handlers": ["console"], "level": "INFO"},
        "referrals": {"handlers": ["console"], "level": "INFO"},
    },
}
