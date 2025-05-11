FROM python:3.12-alpine

# Устанавливаем bash (для Alpine)
RUN apk add --no-cache bash

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p /var/log/app && touch /var/log/app/app.log

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]