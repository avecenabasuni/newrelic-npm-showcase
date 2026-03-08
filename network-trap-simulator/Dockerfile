FROM python:3.11-alpine

WORKDIR /app
COPY generate.py .

RUN pip install --no-cache-dir pysnmp

ENV TRAP_TARGET=ktraps
ENV TRAP_PORT=1620
ENV INTERVAL_SEC=15
ENV INCIDENT_PROBABILITY=0.15

# -u disables python stdout buffering ensuring docker logs are real-time
CMD ["python", "-u", "generate.py"]
