#!/usr/bin/env bash
set -euo pipefail

echo "[migrate] Upgrading database to head..."
alembic upgrade head

echo "[migrate] Current migration:"
alembic current
