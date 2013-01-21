from twisted.scripts import twistd
from twisted.python.usage import Options
import sys
from txdevserver import autoreload
import os

logger_file = os.path.join(os.path.dirname(__file__), 'logger.html')

class TxDevServerOptions(twistd.ServerOptions):
    _optionOverrides = {}

    def parseOptions(self, options=None):
        if options is None and self.defaultSubCommand is None:
            options = sys.argv[1:] or ["--help"]
        Options.parseOptions(self, options)

    def postOptions(self):
        super(TxDevServerOptions, self).postOptions()
        if self._optionOverrides:
            self.update(self._optionOverrides)
sigil = object()

def run(appname=None, appOpts=None, options=None, **kwargs):
    TxDevServerOptions._optionOverrides.update({
        "nodaemon": True, 
        "no_save": True
    })
    
    if appOpts is None:
        appOpts = {}

    appOpts.update({
        "logger_file": logger_file
    })

    if options is not None:
        TxDevServerOptions._optionOverrides.update(options)

    if kwargs:
        TxDevServerOptions._optionOverrides.update(kwargs)

    
    if appOpts is not None:
        TxDevServerOptions.defaultSubCommand = sigil    
    elif appname is not None:
        TxDevServerOptions.defaultSubCommand = appname

    TxDevServerOptions.appOpts = appOpts
    autoreload.main(twistd.app.run, [twistd.runApp, TxDevServerOptions])
