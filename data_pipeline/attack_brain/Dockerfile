FROM python:3.10-slim

WORKDIR /app

# Copy shared models
COPY shared_models.py /app/

# Setup working directory for the microservice
WORKDIR /app/attack_brain

COPY attack_brain/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY attack_brain/ .

CMD ["python", "main.py"]
