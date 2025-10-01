#!/usr/bin/env bash
# exit on error
set -o errexit

# Navigate to the correct directory
cd /opt/render/project/src

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate
