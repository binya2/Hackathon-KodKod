FROM python:3.9-slim

# --- NETFREE CERT INTSALL ---
ADD https://netfree.link/cacert/united/x2/unix.sh /home/netfree-unix-ca.sh 
RUN cat /home/netfree-unix-ca.sh | sh
ENV NODE_EXTRA_CA_CERTS=/etc/ca-bundle.crt
ENV REQUESTS_CA_BUNDLE=/etc/ca-bundle.crt
ENV SSL_CERT_FILE=/etc/ca-bundle.crt    
# --- END NETFREE CERT INTSALL ---

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY ./history_writer/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY . /app/data_pipeline

WORKDIR /app/data_pipeline/history_writer

CMD ["python", "main.py"]
