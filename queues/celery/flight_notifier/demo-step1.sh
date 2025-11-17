#!/bin/bash

# Exit on error
set -e

# Print commands before executing
set -x

logo-ls -lah

read -p "Press enter to continue"

podman ps

read -p "Press enter to continue"

glow pyproject.toml -t -l

read -p "Press enter to continue"

uv sync

read -p "Press enter to continue"

glow models.py -t -l

glow tasks.py -t -l

glow main.py -t -l

pwd | pbcopy

uv run celery -A tasks worker --loglevel=info
