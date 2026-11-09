#!/bin/sh
set -eu

exec uv run --locked python scripts/ngrok_publish.py
