#!/bin/sh
set -eu

# Apply migrations before serving traffic.
alembic upgrade head

# Extra args (e.g. the dev --reload command) replace the default server command.
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

# Only trust X-Forwarded-* from these proxy IPs (comma separated); default: local only.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"
