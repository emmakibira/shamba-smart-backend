#!/bin/bash
# Shamba Smart Backend Development Server
set -e

echo "Starting Shamba Smart Backend..."

# Execute using the explicit path to the venv binary
python manage.py runserver 0.0.0.0:8000
