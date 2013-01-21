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
        if hasattr(record, "extra"):
            self.send_to_all(record.levelname, record.extra)
        else:
            if record.name == 'django.db.backends':
                self.send_to_all("sql", self.format(record))
            else:
                self.send_to_all("manual", self.format(record))

webAppLogHandler = logging.StreamHandler(stream=sys.stdout)
webAppLogHandler.setFormatter(logging.Formatter(fmt=debug_log_format))

webAppLogHandler.setLevel(logging.DEBUG)
webapp_logger.addHandler(webAppLogHandler)


ESLogger = _ESLogger()
ESLogger.setLevel(logging.DEBUG)
webapp_logger.addHandler(ESLogger)
