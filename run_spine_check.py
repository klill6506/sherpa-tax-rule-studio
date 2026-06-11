"""Wrapper: configure Django, then run check_spine_integrity.py.

Needed because the checker imports loader modules that touch Django models;
run with: poetry run python run_spine_check.py
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django

django.setup()

import runpy

runpy.run_path("check_spine_integrity.py", run_name="__main__")
