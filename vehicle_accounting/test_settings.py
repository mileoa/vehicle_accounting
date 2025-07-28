from vehicle_accounting.settings import *

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": ":memory:",
    }
}
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
GRAPHHOPPER_API_KEY = "test_key"
GEOPIFY_API_KEY = "test_key"
ALLOWED_HOSTS = ["*"]
