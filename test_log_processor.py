import os

from collections import deque, defaultdict

from log_processor import get_section, LogEntry, LogFileProcessor


def test_get_section():
    entry = LogEntry('', '', '', None, '', '/twitter/send/34', '', 0, 0)
    assert get_section(entry) == '/twitter'


def test_get_section_for_root():
    entry = LogEntry('', '', '', None, '', '/', '', 0, 0)
    assert get_section(entry) == '/'


def test_alerting():
    try:
        os.remove('offest_test')
    except OSError:
        pass

    msg_queue = deque()
    log_proc = LogFileProcessor(
        './apache.log',
        'offest_test',
        True,
        10,
        defaultdict(int),
        msg_queue,
        patterns=['./apache.log']
    )

    assert msg_queue == deque(
        [
            'recovered: hits=0.016666666666666666, triggered at 2004-03-07 '
            '19:56:50-08:00',
            'alert: hits=10.008333333333333, triggered at 2004-03-07 '
            '17:01:34-08:00',
            'recovered: hits=1.3166666666666667, triggered at 2004-03-07 '
            '16:59:20-08:00',
            'alert: hits=10.008333333333333, triggered at 2004-03-07 '
            '16:57:01-08:00'
        ]
    )


# TODO test stats

# TODO test event changes

# TODO test log parsing
