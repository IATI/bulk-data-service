FROM python:3.12.5-slim-bookworm

RUN apt-get update -y

WORKDIR /bulk-data-service

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ src
COPY db-migrations/ db-migrations

ENTRYPOINT ["/usr/local/bin/python", "src/iati_bulk_data_service.py"]
