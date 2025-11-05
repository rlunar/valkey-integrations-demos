#!/bin/bash

# Exit on error
set -e

# Print commands before executing
set -x

uv run celery -A tasks inspect active

uv run python main.py

uv run celery -A tasks inspect active
