FROM python:3.10-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY ./attack_brain/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/data_pipeline

WORKDIR /app/data_pipeline/attack_brain

CMD ["python", "main.py"]
