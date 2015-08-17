#!/usr/bin/env python
import time
from datetime import datetime
from tornado import httpclient, gen, ioloop, escape, queues

WORKER_NUM = 1000
HOST = 'http://localhost:8888'

def timestamp():
    t = datetime.now()
    return '%02d:%02d:%02d-%06d' % (t.hour, t.minute, t.second, t.microsecond)

def log(info):
	print('%s: %s' % (timestamp(), info))

@gen.coroutine
def poll(idx):
	"""poll messages from /a/message/updates by using long-poll"""
	client = httpclient.AsyncHTTPClient(max_clients=WORKER_NUM)
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
	q.put(WORKER_NUM)

	for i in range(WORKER_NUM):
		worker(i)

	yield q.join()

if __name__ == '__main__':
	log('%d workers is polling. press Control + C to quit.' % WORKER_NUM)
	try:
		ioloop.IOLoop.current().run_sync(main)
	except KeyboardInterrupt as e:
		log('quit.')
