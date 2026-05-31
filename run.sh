#!/bin/bash

# Shamba Smart Backend Development Server

set -e

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "Starting Shamba Smart Backend..."
python manage.py runserver 0.0.0.0:8000
