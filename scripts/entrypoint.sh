#!/bin/bash

echo "Waiting for database to be ready..."
# Si vous utilisez PostgreSQL
# python -c "import time; import psycopg2; time.sleep(5); \
#   while True: \
#     try: psycopg2.connect(host='db', port=5432, user='postgres', password='postgres', dbname='postgres'); break; \
#     except psycopg2.OperationalError: time.sleep(1);"

# Si vous utilisez MySQL
# python -c "import time; import MySQLdb; time.sleep(5); \
#   while True: \
#     try: MySQLdb.connect(host='db', port=3306, user='root', passwd='root', db='django'); break; \
#     except MySQLdb.OperationalError: time.sleep(1);"

echo "Applying database migrations..."
python manage.py migrate

echo "Creating superuser if needed..."
python manage.py createsuperuser --noinput || true

echo "Starting server..."
gunicorn --bind 0.0.0.0:8000 core.wsgi:application