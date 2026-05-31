#!/bin/bash

# Shamba Smart Backend Setup Script

set -e

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Creating environment file..."
cp .env.example .env

echo "Creating migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate

echo "Creating superuser..."
python manage.py createsuperuser

echo "Setup complete!"
echo "To run the development server, use:"
echo "  source .venv/bin/activate && python manage.py runserver 0.0.0.0:8000"
