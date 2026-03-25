FROM python:3.10-slim

# Set the working directory that will be the root for PYTHONPATH
WORKDIR /app

# Add the root directory to PYTHONPATH
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Copy requirements first for layer caching
COPY ./state_aggregator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire project structure into a subdirectory that matches the import path
COPY . /app/data_pipeline

# Set the working directory for the specific service
WORKDIR /app/data_pipeline/state_aggregator

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
