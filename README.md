# Photo Uploading Service

## Описание

Сервис для асинхронной загрузки и обработки изображений с интерактивным фронтендом и API для управления задачами.

## Сервисы проекта

1. **Основной сервис (Django)**
   - Загрузка изображений через веб-интерфейс
   - REST API для управления задачами
   - Серверная валидация загружаемых файлов

2. **Celery Worker**
   - Асинхронная обработка изображений
   - Управление очередями задач
   - Интеграция с внешними сервисами

3. **База данных (PostgreSQL)**
   - Хранение метаданных изображений
   - Хранение результатов обработки изображений

4. **Redis**
   - Брокер сообщений для Celery
   - Backend для Celery

5. **Docker**
   - Контейнеризация сервисов
   - Сборка и запуск сервисов

    
## Особенности реализации
Безопасность:
 - CSRF-токены для всех POST-запросов
 - Строгая валидация на клиенте и сервере

UX-фичи:
   - Интерактивный прогресс-бар
   - Подсветка невалидных файлов
   - Автообновление статуса

Оптимизация:
   - Асинхронная обработка изображений без блокировки интерфейса
   - Пакетная загрузка файлов
   - Поллинг статуса задач

## Подробное описание работы
### Процесс загрузки изображений

1. Пользователь загружает файлы через веб-интерфейс или API
2. Сервер выполняет валидацию:
   - Проверка формата (jpg, png, webp, pdf)
   - Проверка размера (макс. 5MB)
   - Проверка имени файла (макс. 255 символов)
   - Проверка количества файлов (макс. 100 за раз)

3. Валидные файлы передаются в Celery для асинхронной обработки
4. Функция `image_handler` имитирует обрабатку каждого файла, генерируя рандомное число и время выполнения
5. Celery сохраняет результаты в БД и возвращает результаты обработки
6. Пользователь получает:
   - ID задач для отслеживания статуса
   - Список успешно принятых файлов с указанием:
     - названия файла
     - результатов обработки (время выполнения, рандомное число, ID в БД)
     - статуса обработки (PENDING, SUCCESS, FAILURE)

### Отслеживание статуса задач

1. Клиент запрашивает статус по task_id
2. Система проверяет состояние задачи в Celery
3. Возвращает один из статусов:
   - PENDING - в очереди
   - SUCCESS - успешно обработано
   - FAILURE - ошибка обработки

## Запуск приложения

#### Требования
- Python 3.12+
- Docker 20.10+ (для запуска в контейнере)

### Инструкция по запуску

1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/your-repo/photo-uploading-service.git
   cd photo-uploading-service

2. Создать файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```
3. Запустить сервисы:

Запуск через Docker Compose:

```bash
docker-compose up -d --build
```
Запуск и установка на локальную машину:

Установка и активация виртуального окружения:
```bash
python -m venv venv
source venv/bin/activate
```
Установка зависимостей:
```bash
pip install -r requirements.txt
```
Запуск сервисов:
```bash
psql -h localhost -U postgres -W
```

```bash
python manage.py migrate && python manage.py runserver 
```
```bash
celery -A config worker --loglevel=info
```

```bash
redis-server
```

4. Создать суперпользователя (опционально, если планируете пользоваться админ-панелью):
```bash
python manage.py createsuperuser
```
или 
```bash
docker-compose exec django_server python manage.py createsuperuser
```
5. Доступ к сервисам:

- API: http://localhost:8000/api/

- Админка: http://127.0.0.1:8000/admin

6. Ключевые методы API:

- GET */api/* - домашняя страница c формой загрузки

- POST */api/upload/* - Загрузка файлов (выполняется через fetch API)

- GET	*/api/task-status/* - Проверка статуса(выполняется через fetch API)

7. Команды управления для Docker Compose:
Остановка сервисов:

```bash
docker-compose down
```
Просмотр логов:

```bash
docker-compose logs -f
```

Запуск тестов:

```bash
docker-compose exec django_server python manage.py test
```

Пересборка конкретного сервиса:

```bash
docker-compose up -d --build django_server
```