## Система анализа отзывов посетителей театров и концертных залов ГАУК ТО «Тюменского концертно-театрального объединения»

### Подготовка

1. Создать `.env`:

```shell
cp .env.example .env
```

2. Скачать архивы [модели классификации](https://disk.yandex.ru/d/Yvdh_kowqPRo4g) и [модели извлечения аспектов](https://disk.yandex.ru/d/EaUnb_N5DBiJ3g), затем распаковать их в `models`:

```shell
tar -xf ./classification_model.zip -C models
tar -xf ./aspect_extraction_model.zip -C models
```

### Запуск через Docker Compose

```shell
docker compose up --build
```

Доступно после запуска:
- Django API: `http://localhost:8000`
- Микросервис анализа: `http://localhost:8001`
- Healthcheck: `http://localhost:8001/health`

Остановить:

```shell
docker compose down
```

### Локальный запуск

```shell
pip install -r requirements.txt
```

Установить и запустить Redis:

```shell
docker run --name redis-container -d -p 6379:6379 redis
```

Применить миграции:

```shell
python manage.py migrate
```

Запустить микросервис анализа:

```shell
uvicorn analysis_service.main:app --port 8001
```

Создать .env для микросервиса импорта мероприятий с афиши и запустить:

```shell
cp events_worker/.env.example events_worker/.env
uvicorn events_worker.main:app --host 0.0.0.0 --port 8002
```

Запустить Celery и приложение:

```shell
celery -A review_analyser worker -l info -P gevent
python manage.py runserver
```
