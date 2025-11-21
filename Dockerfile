FROM python:3.12.6-slim-bookworm AS builder

RUN apt-get update && apt-get install -y git

ENV VIRTUAL_ENV=/opt/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /bulk-data-service

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.12.6-slim-bookworm

RUN apt-get update -y

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /bulk-data-service

COPY pyproject.toml .

COPY src/ src

COPY db-migrations/ db-migrations

ENTRYPOINT ["python", "src/iati_bulk_data_service.py"]
