FROM python:3.10-slim

WORKDIR /app

# Copy shared models
COPY shared_models.py /app/

# Setup working directory for the microservice
WORKDIR /app/state_aggregator

COPY state_aggregator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY state_aggregator/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
