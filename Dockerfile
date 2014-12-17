FROM ipanousis/armada-docker-register
MAINTAINER Yannis Panousis ipanousis156@gmail.com

RUN apt-get install -y python-redis

ENV NOTIFY python /app/redis-register.py

VOLUME /etc/redis-register

ADD . /app
