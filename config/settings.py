"""
Django settings for American Horse Racing VIP Picker API.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
    "racing",
    "scraper",
    "integrations",
    "referrals",
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
        "DIRS": [],
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

LANGUAGE_CODE = "en-us"
# US East Coast is the primary racing timezone for this product
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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
