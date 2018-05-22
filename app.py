from collections import defaultdict, deque
from threading import Timer
import time
import os
import sys

from blessed import Terminal
from watchdog.observers import Observer

from log_processor import LogFileProcessor

# TODO check if file exists and if log is a correct format
LOG_FILE_DIR = os.environ.get('LOG_FILE_PATH', '/var/log/')
LOG_FILE = os.environ.get('LOG_FILE', 'access.log')
LOG_FILE_PATH = os.path.join(LOG_FILE_DIR, LOG_FILE)

# we are storing the offset here to avoid reading the same lines twice
# using file in the current directory to avoid setting write permissions
# to /var/log/
OFFSET_FILE = os.environ.get('LOG_OFFSET_FILE', './offset')
# Save offset for every line read
PARANOID = os.environ.get('LOG_PARANOID_OFFSET', True)
DASHBOARD_REFRESH_RATE = os.environ.get('DASHBOARD_REFRESH_RATE', 10)
HIGH_TRAFFIC_LIMIT = os.environ.get('HIGH_TRAFFIC_LIMIT', 10)

msg_queue = deque()
stats = defaultdict(int)


def display_stats(stats, msg_queue, term):
    timer = Timer(
        DASHBOARD_REFRESH_RATE, display_stats, [stats, msg_queue, term]
    )
    timer.daemon = True
    timer.start()

    sorted_stats = sorted(stats.items(), key=lambda x: (-x[1], x[0]))
    print(term.bold('Current Stats:'))
    for section, count in sorted_stats:
        print(f'{section}: {count}')

    # we limit to the last 10 messages. To show user some history.
    while len(msg_queue) > 10:
        msg_queue.pop()

    print(term.bold('Alerts history:'))
    if msg_queue and msg_queue[0].startswith('alert'):
        print(term.red('Warning! Alert not recovered'))

    for msg in msg_queue:
        if msg.startswith('alert'):
            print(term.red_reverse(msg))
        else:
            print(term.green_reverse(msg))


if __name__ == '__main__':
    term = Terminal()
    print(term.bold(f'HTTP log monitoring for {LOG_FILE_PATH}'))
    display_stats(stats, msg_queue, term)

    event_handler = LogFileProcessor(
        LOG_FILE_PATH,
        OFFSET_FILE,
        PARANOID,
        HIGH_TRAFFIC_LIMIT,
        stats,
        msg_queue,
        patterns=[LOG_FILE_PATH]
    )
    observer = Observer()
    observer.schedule(event_handler, path=LOG_FILE_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)  # for easy development
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
