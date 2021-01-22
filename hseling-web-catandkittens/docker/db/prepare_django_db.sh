#!/bin/sh
/opt/code/db/start_postgres.sh
echo 'Migrating DB'
python3 manage.py migrate

echo 'Migrating to test DB'
# Copy the database, so we don't run migrations twice
su-exec postgres psql -c "CREATE DATABASE test_$POSTGRES_DB WITH TEMPLATE $POSTGRES_DB"

echo 'Loading fixtures'
# Note the fixtures are not loaded into the test DB
python3 manage.py loaddata ./*/fixtures/*

python3 manage.py shell -c "from django.contrib.auth import get_user_model; \
 User = get_user_model(); User.objects.create_superuser(username=os.environ.get('DJANGO_ADMIN_NAME'), \
   email=os.environ.get('DJANGO_ADMIN_EMAIL'), \
   password=os.environ.get('DJANGO_ADMIN_PASSWORD'))"

/opt/code/db/stop_postgres.sh
