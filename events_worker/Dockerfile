FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY events_worker /app/events_worker

EXPOSE 8002

CMD ["uvicorn", "events_worker.main:app", "--host", "0.0.0.0", "--port", "8002"]
