#!/usr/bin/env bash
# exit on error
set -o errexit

# Find the Django project directory
if [ -d "django_stock/sandbox_2" ]; then
    cd django_stock/sandbox_2
elif [ -d "sandbox_2" ]; then
    cd sandbox_2
else
    echo "Django project directory not found"
    ls -la
    exit 1
fi

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate
