#!/bin/bash

# Exit on error
set -e

# Print commands before executing
set -x

uv run celery -A tasks inspect active

read -p "Press enter to continue"

uv run python main.py

uv run celery -A tasks inspect active
