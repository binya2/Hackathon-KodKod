FROM python:3.11-slim

WORKDIR /app

# Setup working directory for the microservice
WORKDIR /app/log_aggregator

COPY log_aggregator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY log_aggregator/ .

CMD ["python", "main.py"]
