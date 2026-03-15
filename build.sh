#!/usr/bin/env bash
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Node and build frontend
cd client
npm ci
npm run build
cd ..

# Django collectstatic
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input

# Seed initial data (idempotent)
python manage.py seed_sources
