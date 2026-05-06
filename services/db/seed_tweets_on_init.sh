#!/usr/bin/env bash
set -euo pipefail

echo "[seed] checking for tweet archives in /data/tweets ..."

if [ ! -d "/data/tweets" ]; then
  echo "[seed] /data/tweets does not exist; skipping tweet seed."
  exit 0
fi

shopt -s nullglob
inputs=(/data/tweets/*.zip)
shopt -u nullglob

if [ ${#inputs[@]} -eq 0 ]; then
  echo "[seed] no .zip files found in /data/tweets; skipping tweet seed."
  exit 0
fi

echo "[seed] found ${#inputs[@]} archive(s); loading into ${POSTGRES_DB} ..."

# During docker-entrypoint init, postgres is running locally inside this container.
python3 -u /tmp/db/load_tweets_batch.py \
  --db="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" \
  --inputs "${inputs[@]}"

echo "[seed] done."
