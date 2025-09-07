#!/usr/bin/env bash
set -euo pipefail
APP=delivery-tracker-autumn-sea-6631
MID=d8d9269b914708

fly machine exec "$MID" "rm -f /data/database.db" --app "$APP"
fly machine restart "$MID" --app "$APP"

