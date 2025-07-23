run:
	uv run python3 manage.py runserver localhost:8081

run_wsgi:
	uv run  gunicorn --reload vehicle_accounting.wsgi:application --workers 4 --worker-class gevent --bind localhost:8081

run_kafka_consumer:
	uv run python3 kafka_consumer.py

migrate:
	uv run python3 manage.py migrate

makemigrations:
	uv run python3 manage.py makemigrations

test:
	uv run pytest --cov=vehicle_accounting --cov-report=html -n auto --ds=vehicle_accounting.test_settings tests/
