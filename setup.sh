#!/bin/bash

# Shamba Smart Backend Setup Script

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
echo "  python manage.py runserver 0.0.0.0:8000"
