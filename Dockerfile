FROM python:3.9-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "API.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS dagster
EXPOSE 3000
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
