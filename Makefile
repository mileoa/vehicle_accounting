DC = docker compose 
LOGS = docker logs 
ENV = --env-file ./src/.env
EXEC = docker exec -it
MANAGE_PY = python manage.py

STORAGES_FILE = docker/storages.yaml
DB_CONTAINER = example-db

APP_FILE = docker/app.yaml
APP_CONTAINER = vehicle-accounting

TELEGRAM_FILE = docker/telegram.yaml
TELEGRAM_CONTAINER = telegram-bot

KAFKA_FILE = docker/kafka.yaml
KAFKA_CONTAINER = kafka

GPS_SERVICE_FILE = docker/gps-service.yaml
GPS_SERVICE_CONTAINER = gps-service

NGINX_FILE = docker/nginx.yaml
NGINX_CONTAINER = nginx

MONITORING_FILE = docker/monitoring.yaml



.PHONY: storages
storages:
	${DC} -f ${STORAGES_FILE} ${ENV} up -d

.PHONY: storages-down
storages-down:
	${DC} -f ${STORAGES_FILE} down

.PHONY: storages-logs
storages-logs:
	${LOGS} ${DB_CONTAINER} -f

.PHONY: app
app:
	${DC} -f ${APP_FILE} -f ${STORAGES_FILE} -f ${TELEGRAM_FILE} -f ${KAFKA_FILE} -f ${GPS_SERVICE_FILE} -f ${NGINX_FILE} -f ${MONITORING_FILE} ${ENV} up -d

.PHONY: app-rebuild
app-rebuild:
	${DC} -f ${APP_FILE} -f ${STORAGES_FILE} -f ${TELEGRAM_FILE} -f ${KAFKA_FILE} -f ${GPS_SERVICE_FILE} -f ${NGINX_FILE} -f ${MONITORING_FILE} ${ENV} up --build -d

.PHONY: app-logs
app-logs:
	${LOGS} ${APP_CONTAINER} -f

.PHONY: app-down
app-down:
	${DC} -f ${APP_FILE} -f ${STORAGES_FILE} -f ${TELEGRAM_FILE} -f ${KAFKA_FILE} -f ${GPS_SERVICE_FILE} -f ${NGINX_FILE} -f ${MONITORING_FILE} ${ENV} down 

.PHONY: makemigrations
makemigrations:
	${EXEC} ${APP_CONTAINER} ${MANAGE_PY} makemigrations

.PHONY: migrate
migrate:
	${EXEC} ${APP_CONTAINER} ${MANAGE_PY} migrate

.PHONY: superuser
superuser:
	${EXEC} ${APP_CONTAINER} ${MANAGE_PY} createsuperuser

.PHONY: test
test:
	PYTHONPATH=src pytest --cov=src --cov-report=html -n auto --ds=core.settings.test integration_tests
