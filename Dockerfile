FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry poetry-plugin-export

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
