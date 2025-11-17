#!/bin/bash

# Exit on error
set -e

# Print commands before executing
set -x

valkey-cli -h localhost -p 6379 -3 FLUSHDB ASYNC

valkey-cli -h localhost -p 6380 -3 FLUSHDB ASYNC