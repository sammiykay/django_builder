#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command

# Run makemigrations
try:
    call_command('makemigrations', 'ai_builder', verbosity=2)
    print("✅ Migration created successfully")
except Exception as e:
    print(f"❌ Migration failed: {e}")