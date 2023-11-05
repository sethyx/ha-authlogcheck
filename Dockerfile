FROM python:3.11-slim-bookworm

RUN pip install requests

COPY . .

CMD python ha-logtail.py
