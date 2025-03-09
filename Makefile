run:
	uv run python3 manage.py runserver localhost:8081

migrate:
	uv run python3 manage.py migrate

makemigrations:
	uv run python3 manage.py makemigrations

test:
	uv run python3 manage.py test 