FROM python:3.10-slim

WORKDIR /app

# Copy shared models
COPY shared_models.py /app/

# Setup working directory for the microservice
WORKDIR /app/recon_brain

COPY recon_brain/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY recon_brain/ .

CMD ["python", "main.py"]
