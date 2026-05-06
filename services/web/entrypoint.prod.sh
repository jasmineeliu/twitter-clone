#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z $SQL_HOST $SQL_PORT; do
  sleep 1
done

echo "Postgres started"

exec uvicorn main:app --host 0.0.0.0 --port 5000 --reload
