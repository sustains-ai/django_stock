#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create staticfiles directory if it doesn't exist
mkdir -p staticfiles

# Collect static files with verbose output
python manage.py collectstatic --noinput --clear --verbosity=2

# List collected static files for debugging
echo "=== Static files collected ==="
ls -la staticfiles/
echo "=== CSS files ==="
ls -la staticfiles/css/ || echo "No CSS directory found"

# Run migrations
python manage.py migrate
