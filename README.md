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

Установить и запустить OpenSearch

```shell
docker run -it -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" --name opensearch-node -d --env-file .env opensearchproject/opensearch:latest
```

Скачать [архив модели классификации](https://disk.yandex.ru/d/Yvdh_kowqPRo4g) и распаковать содержимое в директорию:
```shell
tar -xf ./classification_model.zip -C models
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
