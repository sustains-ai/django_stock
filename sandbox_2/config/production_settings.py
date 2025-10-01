# Production settings for Render deployment
from .settings import *

# Ensure static files are served correctly in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Ensure static files are collected
STATIC_ROOT = BASE_DIR / "staticfiles"

# Debug static files in production
import logging
logging.basicConfig(level=logging.DEBUG)
