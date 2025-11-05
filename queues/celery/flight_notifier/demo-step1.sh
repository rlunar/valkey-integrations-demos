#!/bin/bash

# Exit on error
set -e

# Print commands before executing
set -x

podman ps

read -p "Press enter to continue"

glow pyproject.toml -t -l

uv sync

glow models.py -t -l

glow tasks.py -t -l

glow main.py -t -l

pwd | pbcopy

uv run celery -A tasks worker --loglevel=info
