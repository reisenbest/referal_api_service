FROM python:3.11-alpine3.16

COPY requirements.txt /temp/requirements.txt

COPY stakewolle_api_service /stakewolle_api_service

WORKDIR /stakewolle_api_service

EXPOSE 8000

RUN apk add postgresql-client build-base postgresql-dev

RUN pip install -r /temp/requirements.txt


RUN adduser -D service-user


USER service-user


