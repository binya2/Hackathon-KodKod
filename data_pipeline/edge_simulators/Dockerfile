FROM python:3.10-slim

WORKDIR /app

# Copy shared models
COPY shared_models.py /app/

# Setup working directory for the microservice
WORKDIR /app/edge_simulators

COPY edge_simulators/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY edge_simulators/ .

# Command is overridden in docker-compose.yml
CMD ["python", "drones_sim.py"]
