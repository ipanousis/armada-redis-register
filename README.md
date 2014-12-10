Runs a docker-gen container with a template that registers containers to redis for hipache

Define environment variable FLOCKER_DOMAIN to your.own.domain for container http endpoints to be
forwarded as e.g.:

etcd.your.own.domain:80 -> your.own.domain:4001
