FROM python:3.11-slim

ENV CELERY_VERSION 5.3.1
ENV REDIS_VERSION 4.6.0

RUN pip install --upgrade pip setuptools wheel \
    pip install celery~="$CELERY_VERSION" \
    pip install redis~="$REDIS_VERSION"
