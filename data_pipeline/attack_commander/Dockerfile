FROM python:3.10-slim

WORKDIR /app

# Copy shared models
COPY shared_models.py /app/

# Setup working directory for the microservice
WORKDIR /app/attack_commander

COPY attack_commander/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY attack_commander/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
