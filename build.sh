#!/usr/bin/env bash
set -o errexit

# Install Python dependencies
pip install poetry
poetry config virtualenvs.create false
poetry install --no-interaction --no-ansi

# Install Node and build frontend
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs || true  # May already be installed on Render
cd client
npm ci
npm run build
cd ..

# Django collectstatic
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input
