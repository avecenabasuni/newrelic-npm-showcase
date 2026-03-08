FROM python:3.11-alpine

WORKDIR /app
COPY generate.py .

ENV SYSLOG_TARGET=ksyslog
ENV SYSLOG_PORT=5143
ENV INTERVAL_SEC=10
ENV INCIDENT_PROBABILITY=0.15

# -u to disable python stdout buffering ensuring docker logs are real-time
CMD ["python", "-u", "generate.py"]
