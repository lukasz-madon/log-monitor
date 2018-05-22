# log-monitor

HTTP log monitor - console application.


## Dependencies

pygtail - reads log file lines that have not been read and stores offset.
python-dateutil - parsing timestamps.
watchdog - used for system agnostic file watching.


## Installation

Required pipenv.org. After installation just run `pipenv install`. It should install all dependencies (including python 3.6).

## Running

```
rm offest  # remove the offset file if exists
LOG_FILE=apache.log python app.py # without the LOG_FILE /var/log/access.log will be used
```


## Testing

```
echo '64.242.88.10 - - [07/Mar/2004:16:56:50 -0800] "GET /twiki/bin HTTP/1.1" 200 8545' >> apache.log
```

## Future improvments

- create a library from pygtail and watchdog (remove extra complexity, read logs back for the total traffic alert)
- configuration file
- Gevent and multiprocessing
- asyncio
- DB (offset and sending a message in a transaction)
- rate-limiting ?
