FROM python:latest

WORKDIR /app

COPY ./ /app/

RUN pip install -r src/requirements.txt

ENV TOKEN=""

EXPOSE 6969 8080

CMD [ "python", "src/main.py" ]