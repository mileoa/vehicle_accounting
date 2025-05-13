#!/bin/bash

# Скрипт для автоматического деплоя проекта учета транспортных средств
# Используется для деплоя с использованием Docker

# Цвета для вывода в консоль
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода сообщений со статусом
function log_message() {
    local level=$1
    local message=$2
    
    case $level in
        "info")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "warn")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "error")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        *)
            echo -e "$message"
            ;;
    esac
}

# Функция для проверки наличия установленной программы
function check_requirement() {
    local command=$1
    local package=$2
    
    if ! command -v $command &> /dev/null; then
        log_message "error" "$command не найден. Пожалуйста, установите $package и запустите скрипт снова."
        exit 1
    fi
}

# Проверка наличия требуемых программ
log_message "info" "Проверка требований для деплоя..."
check_requirement "docker" "Docker"
check_requirement "docker-compose" "Docker Compose"
check_requirement "git" "Git"

# Настройка переменных окружения и параметров
REPO_URL=${REPO_URL:-"git@github.com:mileoa/vehicle_accounting.git"}
BRANCH=${BRANCH:-"main"}
PROJECT_DIR=${PROJECT_DIR:-"$HOME/vehicle_accounting"}
DOCKER_COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yaml"


# Клонирование репозитория (или обновление, если уже существует)
function clone_or_update_repo() {
    if [ -d "$PROJECT_DIR" ]; then
        log_message "info" "Проект уже существует в $PROJECT_DIR. Обновление..."
        cd "$PROJECT_DIR"
        git fetch
        git reset --hard origin/$BRANCH
    else
        log_message "info" "Клонирование репозитория $REPO_URL в $PROJECT_DIR..."
        git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
}

# Остановка и удаление контейнеров, если они уже запущены
function clean_docker() {
    log_message "info" "Остановка и удаление запущенных контейнеров проекта..."
    cd "$PROJECT_DIR"
    docker-compose down -v 2>/dev/null || true
}

# Запуск Docker Compose
function start_docker() {
    log_message "info" "Запуск контейнеров Docker..."
    cd "$PROJECT_DIR"
    
    # Запускаем Docker Compose
    docker-compose up -d
    
    if [ $? -ne 0 ]; then
        log_message "error" "Не удалось запустить Docker контейнеры"
        exit 1
    fi
    
    log_message "info" "Docker контейнеры запущены успешно"
}

function check_docker_running() {
    log_message "info" "Проверка состояния Docker..."
    
    # Проверяем, установлен ли Docker
    check_requirement "docker" "Docker"
    check_requirement "docker-compose" "Docker Compose"
    
    # Проверяем, запущен ли сервис Docker
    if ! docker info &>/dev/null; then
        log_message "error" "Docker не запущен. Запустите Docker и попробуйте снова.."
        exit 1
    fi
}

# Сбор статических файлов
function collect_static() {
    log_message "info" "Сбор статических файлов..."
    cd "$PROJECT_DIR"
    docker-compose exec -T web python manage.py collectstatic --noinput
    
    if [ $? -ne 0 ]; then
        log_message "warn" "Не удалось собрать статические файлы"
    else
        log_message "info" "Статические файлы собраны успешно"
    fi
}

# Вывод информации о доступе к приложению
function show_access_info() {
    local ip_address=$(hostname -I | awk '{print $1}')
    
    log_message "info" "Деплой завершен успешно!"
    log_message "info" "Приложение доступно по адресу:"
    log_message "info" "* Локально: http://localhost:8000"
    
    log_message "info" "Для остановки выполнить:"
    log_message "info" "cd $PROJECT_DIR && docker-compose down"
}

# Основная функция
function main() {
    log_message "info" "Начинаем процесс деплоя..."
    
    # Выполнение основных шагов деплоя
    clone_or_update_repo
    clean_docker
    start_docker
    collect_static
    show_access_info
}

# Запуск основной функции
main