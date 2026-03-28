FROM python:3.10-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY ./edge_simulators/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire pipeline structure to maintain `data_pipeline.shared` paths
COPY . /app/data_pipeline

WORKDIR /app/data_pipeline/edge_simulators

# Command is overridden in docker-compose.yml
CMD ["python", "drones_sim.py"]
