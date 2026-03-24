FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir \
    torch==2.9.1 \
    torchvision==0.24.1 \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

RUN python -c "import nltk; nltk.download('stopwords', quiet=True)"

COPY analysis_service /app/analysis_service

EXPOSE 8001

CMD ["uvicorn", "analysis_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
