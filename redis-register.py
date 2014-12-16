#!/usr/bin/python

import json,os,sys,redis,time
import logging
import re

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


#redisAdd = os.environ['REDIS'].split(":")

#rs = redis.Redis(redisAdd[0], int(redisAdd[1]))

#obj = requests.get("http://"+os.environ['ETCD']+"/v2/keys/backends/?recursive=true").json()

#backends = obj['node']['nodes']

backends = json.loads(open('/tmp/containers.json','r').read())['containers']

print 'Total backends: %d' % len(backends)

redis_host_port = os.environ['REDIS_HOST'].split(':')
redis_port = (int(redis_host_port[1]) if len(redis_host_port) == 2 else 6379)
rs = redis.Redis(redis_host_port[0], redis_port)

get_port_protocol = lambda port : 'https' if int(port) == 443 else 'http'

for svc in backends:

  logging.info(svc)

  if not 'flocker--' in svc['name']:
    continue

  svc_name = svc['name'].replace('flocker--','')

  exposed_ports = [port for port in svc['ports'] if port['external'] != None]
  if len(exposed_ports) > 0:
    exposed_port = exposed_ports[0]
    redis_svc = Service(svc_name, svc_name + '.' + CLUSTER_NAME, get_port_protocol(exposed_port['internal']) + '://' + CLUSTER_NAME + ':' + exposed_port['external'] )
    print 'Redis Entry: (id, host, instance) = (%s, %s, %s)' % (redis_svc.id, redis_svc.host, redis_svc.instance)
    updateProxy(redis_svc, rs)


  for exposed_port in exposed_ports:
    redis_svc_name = exposed_port['internal'] + '.' + svc_name
    redis_svc = Service(redis_svc_name, redis_svc_name + '.' + CLUSTER_NAME, get_port_protocol(exposed_port['internal']) + '://' + CLUSTER_NAME + ':' + exposed_port['external'] )
    print 'Redis Entry: (id, host, instance) = (%s, %s, %s)' % (redis_svc.id, redis_svc.host, redis_svc.instance)
    updateProxy(redis_svc, rs)

logging.info("exiting...")
