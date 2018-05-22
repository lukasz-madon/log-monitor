from collections import defaultdict, deque
from threading import Timer
import time
import os

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


def display_stats(stats):
    t = Timer(DASHBOARD_REFRESH_RATE, display_stats, [stats])
    t.daemon = True
    t.start()
    print("Alerts", msg_queue)
    print("Stats")
    for section, count in stats.items():
        print(f"{section}: {count}")


# while True:
#     entry = log_queue.get()
#     if not entry:
#         break
#     section = get_section(entry)
#     stats[section] += 1
#     log_queue.task_done()

if __name__ == "__main__":
    display_stats(stats)
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
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
