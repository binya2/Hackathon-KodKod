FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY ./log_aggregator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/data_pipeline

WORKDIR /app/data_pipeline/log_aggregator

CMD ["python", "main.py"]
