from twisted.scripts import twistd
from twisted.python.usage import Options
import os
import sys
from txdevserver import autoreload
logger_file = os.path.join(os.path.dirname(__file__), 'logger.html')


class TxDevServerOptions(twistd.ServerOptions):
    _optionOverrides = {}

    def parseOptions(self, options=None):
        if options is None or ('txdevserver' not in sys.argv):
            options = ['txdevserver'] + sys.argv[1:]
        return Options.parseOptions(self, options)

    def postOptions(self):
        super(TxDevServerOptions, self).postOptions()
        if self._optionOverrides:
            self.update(self._optionOverrides)


def run(options=None, **kwargs):
    TxDevServerOptions._optionOverrides.update({
        "nodaemon": True,
        "no_save": True
    })

    if options is not None:
        TxDevServerOptions._optionOverrides.update(options)

    if kwargs:
        TxDevServerOptions._optionOverrides.update(kwargs)

    autoreload.main(twistd.app.run, [twistd.runApp, TxDevServerOptions])
