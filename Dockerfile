FROM ipanousis/armada-docker-register
MAINTAINER Yannis Panousis ipanousis156@gmail.com

RUN apt-get install -y python-redis

ADD . /app

ENV NOTIFY python /app/redis-register.py
