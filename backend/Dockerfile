FROM python:3.11-slim

WORKDIR /app

COPY . /app

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
