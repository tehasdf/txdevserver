import logging
import time
from txdevserver.eventsource import EventSource
import sys

webapp_logger = logging.getLogger('webapp.request')


def log_request(error=None, request=None, start_time=None, start_queries=0, params_factory=None):
    time_taken = (time.time() - start_time) * 1000
    extra = {
        "time": time_taken,
        "method": request.method,
        "uri": request.uri,
        "code": request.code,
    }
    extra.update(params_factory())
    webapp_logger.info("{1:.0f}ms {0.method} {0.uri} -- {0.code}".format(request, time_taken),
        extra={"extra": extra})


webapp_logger.setLevel(logging.DEBUG)


debug_log_format = (
'-' * 80 + '\n' +
'%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
'%(message)s\n'
)


class _ESLogger(logging.Handler, EventSource):
    def emit(self, record):
        if hasattr(record, 'extra'):
            data = record.extra
        else:
            data = {}

        data['name'] = record.name
        data['level'] = record.levelname
        data['text'] = self.format(record)
        self.send_to_all(record.name, data)


ESLogger = _ESLogger()
ESLogger.setLevel(logging.DEBUG)
logging.root.addHandler(ESLogger)
