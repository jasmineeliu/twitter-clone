# Dockerizing Flask with Postgres, Gunicorn, and Nginx

![Build Status](https://github.com/jasmineeliu/flask-on-docker/actions/workflows/build-dev.yml/badge.svg)

## Overview

This project containerizes Flask with PostgreSQL as its database for development. It is also production-ready, using Gunicorn and Nginx. The app can handle both static and user-uploaded media files and includes a simple endpoint for uploading files.  

## Demo

With the app, users can upload a media file and view it at `localhost:1089/media/file_name`. Users can also view static files at `localhost:1089/static/file_name`. 
![Demo of the App working](./app-demo.gif)

## Building and Running the Application

To start developing, you'll need:

- Flask v2.3.2
- Docker v23.0.5
- Python v3.11.3

Once you've installed these tools, clone this repo through:

```
git clone https://github.com/jasmineeliu/flask-on-docker.git
```

For development mode, use the following commands:


```bash
# To build a new image and bring up your containers in development mode
docker compose up -d --build

# Then, to create your PostgreSQL table in development mode:
docker compose exec web python manage.py create_db
```

For production mode, use the following commands:

```bash
# To build a new image and bring up your containers in production mode
docker compose -f docker-compose.prod.yml up -d --build

# Then, to create your PostgreSQL table in production mode: 
docker compose -f docker-compose.prod.yml exec web python manage.py create_db
```

