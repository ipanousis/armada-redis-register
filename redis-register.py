#!/usr/bin/python

import json,os,sys,redis,time,yaml
import logging
import re

from ConfigParser import ConfigParser

logging.basicConfig(level=logging.DEBUG,filename='/tmp/redis-register.log')

CLUSTER_NAME=os.environ['FLOCKER_DOMAIN']

# in a but not b
def diff(a, b):
	b = set(b)
	return [aa for aa in a if aa not in b]

def intersect(a, b):
	return list(set(a) & set(b))



class Service:

  def __init__(self, id, host, instance):
    self.id = id
    self.host = host
    self.instance = instance


def updateProxy(svc, rs):
  key = "frontend:" + svc.host

  if not rs.exists(key):
    rs.rpush(key, svc.id)

  rs.expire(key, 15)

  existing = rs.lrange(key, 0, -1)

  current = [svc.instance]
  current.insert(0, svc.id)

  toDelete = diff(existing, current)
  toAdd = diff(current, existing)

  for val in toDelete:
    logging.info("D "+key+" "+val)
    rs.lrem(key, val)

  for val in toAdd:
    logging.info("A "+key+" "+val)
    rs.rpushx(key, val)	

containers_string = open('/tmp/containers.json','r').read()
backends = yaml.load(containers_string)['containers']

redis_host_port = os.environ['REDIS_HOST'].split(':')
redis_port = (int(redis_host_port[1]) if len(redis_host_port) == 2 else 6379)
rs = redis.Redis(redis_host_port[0], redis_port)

REDIS_REGISTER_PROPERTIES='/etc/redis-register/redis-register.properties'
redirect_https_enabled = False
redirect_https_host = None
if os.path.exists(REDIS_REGISTER_PROPERTIES):
  properties = ConfigParser()
  properties.readfp(open(REDIS_REGISTER_PROPERTIES,'r'))
  redirect_https_enabled = properties.getboolean('redirect-https', 'enabled')
  redirect_https_host = properties.get('redirect-https', 'host')

def new_service(svc_name, exposed_port):
  def is_https(port):
    return int(port) == 443
  protocol = 'http'
  url = 'http://' + CLUSTER_NAME + ':' + exposed_port['external']
  if is_https(exposed_port['internal']) and redirect_https_enabled:
    url = 'http://' + redirect_https_host + '/' + svc_name
  redis_svc = Service(svc_name, svc_name + '.' + CLUSTER_NAME, url)
  print 'Redis Entry: (id, host, instance) = (%s, %s, %s)' % (redis_svc.id, redis_svc.host, redis_svc.instance)
  return redis_svc

for svc in backends:

  logging.info(svc)

  if not 'flocker--' in svc['name']:
    continue

  svc_name = svc['name'].replace('flocker--','')

  exposed_ports = [port for port in svc['ports'] if port['external'] != None]
  if len(exposed_ports) > 0:
    exposed_port = exposed_ports[0]
    updateProxy(new_service(svc_name, exposed_port), rs)

  for exposed_port in exposed_ports:
    redis_svc_name = exposed_port['internal'] + '.' + svc_name
    updateProxy(new_service(redis_svc_name, exposed_port), rs)

logging.info("exiting...")
