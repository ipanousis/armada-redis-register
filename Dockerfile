FROM ubuntu:14.04
MAINTAINER Yannis Panousis ipanousis156@gmail.com

RUN apt-get update
RUN apt-get install -y wget python python-pip python-dev python-redis python-requests libssl-dev libffi-dev bash

RUN mkdir /app
WORKDIR /app

RUN wget https://github.com/jwilder/docker-gen/releases/download/0.3.6/docker-gen-linux-amd64-0.3.6.tar.gz
RUN tar xvzf docker-gen-linux-amd64-0.3.6.tar.gz -C /usr/local/bin

ADD . /app

ENV DOCKER_HOST unix:///var/run/docker.sock

CMD docker-gen -interval 10 -watch -notify "python /tmp/redis-register.py" redis.tmpl /tmp/redis-register.py
