#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker-compose down
rm -rf chroma/* data/processed/*
mkdir -p chroma data/processed data/source
docker-compose build --no-cache
docker-compose up -d

until curl --fail --silent http://localhost:8000/health >/dev/null; do
  sleep 2
done

curl --fail --silent --show-error \
  -X POST http://localhost:8000/ingest \
  -F action=corpus
printf '\nCorpus rebuilt from scratch.\n'