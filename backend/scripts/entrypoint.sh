#!/bin/sh
if [ "$SEED_DEMO" = true ]; then
  python scripts/seed_demo.py || printf 'Studio demo seed failed\n' >&2
fi
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
