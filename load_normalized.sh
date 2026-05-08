#!/bin/sh

PYTHONUNBUFFERED=1 python3 -u load_tweets.py --db=postgresql://postgres:pass@localhost:2089/postgres_dev --inputs "$1"
