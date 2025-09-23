## Система анализа отзывов посетителей театров и концертных залов ГАУК ТО «Тюменского концертно-театрального объединения»

### Установка и запуск

Создать `.env`-файл по аналогии с `.env.example`

Установка зависимостей

```shell
pip install -r requirements.txt
```

Установить и запустить Redis

```shell
docker run --name redis-container -d -p 6379:6379 redis
```

Примененить миграции

```shell
python manage.py migrate
```

Запустить Celery и само приложение

```shell
celery -A review_analyser worker -l info -P gevent
python manage.py runserver
```
