FROM --platform=linux/amd64 python:3.11-slim-bookworm

RUN pip install requests

COPY . .

CMD python -u ha-logtail.py
