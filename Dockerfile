FROM --platform=linux/amd64 python:slim

RUN pip install requests

COPY . .

CMD python -u ha-logtail.py
