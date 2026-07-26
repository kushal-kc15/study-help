web: daphne -b 0.0.0.0 -p $PORT studyhelp.asgi:application
release: python manage.py migrate && python manage.py collectstatic --noinput
