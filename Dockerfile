FROM python:3.9-alpine

WORKDIR /app

RUN apk add --no-cache ffmpeg

COPY ./src /app

RUN pip install -r requirements.txt

ENV MONGODB_CONNECTION="" FRONTEND_USER="admin" FRONTEND_PASSWORD="admin" ADDRESS="0.0.0.0" BEHIND_PROXY="false"

VOLUME [ "/downloads" ]

EXPOSE 6969 8080

CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:6969 backend:app & gunicorn -w 2 -b 0.0.0.0:8080 frontend.frontend:app" ]