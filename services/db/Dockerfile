FROM postgis/postgis:13-3.5

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    less \
    make \
    vim \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/db

RUN mkdir /data && chown postgres /data

# python deps for load_tweets_batch.py
RUN pip3 install --no-cache-dir psycopg2-binary sqlalchemy

# copy over the pagila database;
# we rename the files so that they get executed in the correct order
COPY schema.sql /docker-entrypoint-initdb.d/01.sql
