import os
import redis
from rq import Worker, Queue, Connection
import sys
import argparse

parser = argparse.ArgumentParser(description='Run the Fax Robot Worker.')
parser.add_argument('--listen', nargs=1, help='Listen queue: high|default|low')
parser.add_argument('--device', nargs=1, help='Modem device to use for faxing')

args = parser.parse_args()

if args.listen:
    listen = args.listen[0].split(',')
else:
    listen = ['high', 'default', 'low']

MODEM_DEVICE = args.device[0] if args.device else '/dev/ttyUSB0'

print >> sys.stderr, "Binding to modem device: " + MODEM_DEVICE

conn = redis.from_url(os.environ.get('REDIS_URI'))

if __name__ == '__main__':
    with Connection(conn):
        Worker.MODEM_DEVICE = MODEM_DEVICE
        worker = Worker(map(Queue, listen))
        worker.work()
