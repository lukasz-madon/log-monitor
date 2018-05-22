from collections import deque
from datetime import datetime
import re
from typing import List, NamedTuple

from dateutil.parser import parse
from pygtail import Pygtail
from watchdog.events import PatternMatchingEventHandler

LOGPATS = r'(\S+) (\S+) (\S+) \[(.*?)\] "(\S+) (\S+) (\S+)" (\S+) (\S+)'

LOGPAT = re.compile(LOGPATS)

ALERT_WINDOW = 2 * 60  #2 mins in seconds

class LogEntry(NamedTuple):
    host: str
    referrer: str
    user: str
    timestamp: datetime
    method: str
    request: str
    proto: str
    status: int
    bytes: int


class LogFileProcessor(PatternMatchingEventHandler):
    """
    Process a single file and send messages to dashboard.

    Should be used as a watchdog handler
    """

    def __init__(
        self,
        log_file,
        offset_file,
        paranoid,
        traffic_limit,
        stats,
        msg_queue,
        patterns=None
    ):
        super().__init__(patterns=patterns)
        self.log_file = log_file
        self.offset_file = offset_file
        self.paranoid = paranoid
        self.traffic_limit = traffic_limit
        self.traffic = 0
        self.stats = stats
        self.msg_queue = msg_queue
        self.error_state = False
        # Python deque is atomic (threadsafe), no need for locking
        # We could discuss what we can do in case the website has enormous
        # amount of traffic (reducing the alerting window, throttling, maxlen)
        self.log_queue = deque()
        self.read_log()

    def on_modified(self, _event):
        """handler triggered when the file is modified"""
        self.read_log()

    def check_alert(self, request_rate, end_time):
        """check if the request rate is over the limit and raises alert"""
        if request_rate > self.traffic_limit:
            if not self.error_state:
                self.msg_queue.appendleft(
                    f"alert: hits={request_rate}, triggered at {end_time}"
                )
                self.error_state = True
        else:
            if self.error_state:
                self.msg_queue.appendleft(
                    f"recovered: hits={request_rate}, triggered at {end_time}"
                )
                self.error_state = False

    def read_log(self):
        """read logs file and puts the result on the queue"""
        for line in Pygtail(self.log_file, self.offset_file, self.paranoid):
            if line == "\n":
                continue

            entry = parse_log_line(line)
            section = get_section(entry)
            self.stats[section] += 1
            self.log_queue.appendleft(entry)

            end_time = self.log_queue[0].timestamp
            start_time = self.log_queue[-1].timestamp
            request_rate = len(self.log_queue) / ALERT_WINDOW
            self.stats['request_rate'] = request_rate
            self.check_alert(request_rate, end_time)

            while self.log_queue and (
                end_time - start_time
            ).seconds > ALERT_WINDOW:
                self.log_queue.pop()
                start_time = self.log_queue[-1].timestamp


def parse_log_line(line: str) -> LogEntry:
    """parses a single line of a log file in Common Log Format"""
    match = LOGPAT.match(line)
    if not match:
        # we could catch that error and skip the line
        raise ValueError(f'incorrect log format: {line}')

    entry = match.groups()
    parsed_time = parse(entry[3][:11] + ' ' + entry[3][12:])
    size = int(entry[8]) if entry[8] != '-' else 0
    return LogEntry(
        entry[0], entry[1], entry[2], parsed_time, entry[4], entry[5],
        entry[6], int(entry[7]), size
    )


def get_section(entry: LogEntry) -> str:
    """returns the section of the request (/twiki/bin/edit/Main -> /twiki)"""
    section = entry.request.split('/')[:2]
    return '/'.join(section)
