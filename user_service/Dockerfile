FROM python:3.12.3

WORKDIR /user_service

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
