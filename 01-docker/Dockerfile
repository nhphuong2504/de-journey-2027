FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir pandas sqlalchemy psycopg2-binary
COPY ingest_data.py .
ENTRYPOINT ["python", "ingest_data.py"]