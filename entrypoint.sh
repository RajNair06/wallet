#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

case "$1" in
    *dramatiq*)
        echo "Main process is dramatiq worker; skipping background worker."
        ;;
    *)
        echo "Starting dramatiq worker in background..."
        dramatiq workers &
        ;;
esac

exec "$@"
