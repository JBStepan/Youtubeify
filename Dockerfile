FROM python:3.9-alpine

WORKDIR /app

RUN apk add --no-cache ffmpeg

COPY ./src /app

RUN pip install -r requirements.txt

ENV MONGODB_CONNECTION="" FRONTEND_USER="" FRONTEND_PASSWORD="" ADDRESS="0.0.0.0" BEHIND_PROXY=false

VOLUME [ "/downloads" ]

EXPOSE 6969 8080

CMD [ "python", "main.py" ]