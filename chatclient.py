#!/usr/bin/env python
import time
from datetime import datetime
from tornado import httpclient, gen, ioloop, escape, queues

MAX_CLIENTS = 500
HOST = 'http://localhost:8888'

def timestamp():
    t = datetime.now()
    return '%02d:%02d:%02d-%06d' % (t.hour, t.minute, t.second, t.microsecond)

def log(info):
	print('%s: %s' % (timestamp(), info))

@gen.coroutine
def poll(idx):
	"""poll messages from /a/message/updates by using long-poll

	In windows, tornado use select() to implement io loop, for windows 7 professional, 
	it's limitation is 512.

	Tornado should run on any Unix-like platform, although for the best performance 
	and scalability only Linux (with epoll) and BSD (with kqueue) are recommended 
	for production deployment (even though Mac OS X is derived from BSD and supports 
	kqueue, its networking performance is generally poor so it is recommended only 
	for development use). Tornado will also run on Windows, although this configuration 
	is not officially supported and is recommended only for development use.

	Platforms: http://www.tornadoweb.org/en/stable/index.html
	Running and deploying: http://www.tornadoweb.org/en/stable/guide/running.html
	"""
	client = httpclient.AsyncHTTPClient(max_clients=MAX_CLIENTS)
	log('worker#%05d: polling from %s' % (idx, HOST))
	body = {'_xsrf': 'undefined'}
	rsp = yield client.fetch(HOST + "/a/message/updates", 
		method='POST', 
		body=escape.json_encode(body),
		request_timeout=0)
	response = escape.json_decode(rsp.body)
	for m in response['messages']:
		log('worker#%05d: [body: %s, id: %s]' % (idx, m['body'], m['id']))

@gen.coroutine
def worker(idx):
	"""worker routine for poll"""
	log('worker#%05d: starting' % idx)
	while True:
		yield poll(idx)

@gen.coroutine
def main():
	"""main"""
	q = queues.Queue()
	q.put(MAX_CLIENTS)

	for i in range(MAX_CLIENTS):
		worker(i)

	yield q.join()

if __name__ == '__main__':
	log('%d workers is polling. press Control + C to quit.' % MAX_CLIENTS)
	try:
		ioloop.IOLoop.current().run_sync(main)
	except KeyboardInterrupt as e:
		log('quit.')
