from txdevserver.loggers import ESLogger
from functools import partial
import time
import sys
import os

from twisted.web.resource import Resource, NoResource
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor

from twisted.web.static import File
from txdevserver.loggers import log_request
from txdevserver.importer import import_string
import os.path

from txdevserver.autoreload import code_changed
from twisted.internet.task import LoopingCall
from twisted.python.rebuild import rebuild
import logging

_win = (sys.platform == "win32")


class LoggedWSGIResource(WSGIResource):
    additional_log_params = lambda res: lambda: {'queries': 0}

    def __init__(self, reactor, threadPool, app, additional_log_params=None):
        super(LoggedWSGIResource, self).__init__(reactor, threadPool, app)
        if additional_log_params:
            self.additional_log_params = additional_log_params

    def render(self, request):
        additional_log_params = self.additional_log_params()
        request.notifyFinish().addCallback(partial(log_request, request=request,
            start_time=time.time(), params_factory=additional_log_params))
        return super(LoggedWSGIResource, self).render(request)


class DevServer(Resource, object):
    def __init__(self, options):
        super(DevServer, self).__init__()
        for url_part, static_path in options['static'].iteritems():
            static_resource = File(static_path)
            self.putChild(url_part, static_resource)

        for url_part, resource_path in options['resources'].iteritems():
            resource = import_string(resource_path)
            self.putChild(url_part, resource)

        logger_file = os.path.join(os.path.dirname(__file__), 'logger.html')
        logger_static = File(logger_file)

        self.putChild("log", logger_static)
        self.putChild("log_es", ESLogger)

        self.attach_app(options)

        self.reloader = LoopingCall(self.check_and_reload, options)
        self.reloader.start(2, now=True)

        self._mtimes = {}

        self.logger = logging.getLogger('webapp.devserver')

    def code_changed(self):
        changed = []
        for filename, module in [(getattr(module, '__file__'), module) for module in sys.modules.values() if hasattr(module, '__file__')]:
            if filename.endswith(".pyc") or filename.endswith(".pyo"):
                filename = filename[:-1]
            if not os.path.exists(filename):
                continue  # File might be in an egg, so it can't be reloaded.
            stat = os.stat(filename)
            mtime = stat.st_mtime
            if _win:
                mtime -= stat.st_ctime
            if filename not in self._mtimes:
                self._mtimes[filename] = mtime
                continue
            if mtime != self._mtimes[filename]:
                changed.append(module)
        if changed:
            self._mtimes = {}
            return changed
        return False

    def getChild(self, path, request):
        request.postpath.insert(0, request.prepath.pop(0))
        return getattr(self, 'app')

    def attach_app(self, subOptions):
        fromAppOpts = subOptions.parent.get('appOpts', {}).get('app')
        if fromAppOpts is not None:
            app = fromAppOpts
        elif subOptions['app'] is not None:
            app = import_string(subOptions['app'])
        else:
            # no app nor app import path given, let's guess!
            files_in_cwd = os.listdir(os.getcwd())
            if 'manage.py' in files_in_cwd:
                from txdevserver.django_helpers import get_django_app
                django_app = get_django_app('manage.py')
                if django_app is not None:
                    app = django_app

        rv = LoggedWSGIResource(reactor, reactor.getThreadPool(), app,
            subOptions.get('log_data_factory'))

        self.app = rv

    def check_and_reload(self, subOptions):
        modules_changed = code_changed()
        if modules_changed:
            for module in modules_changed:

                try:
                    rebuild(module)
                except Exception as e:
                    self.logger.critical("Error reloading %s: %s", module.__name__, e)
                    self.app = NoResource("There was an error reloading the app.")
                    break
                else:
                    self.logger.critical("Reloaded %s (%d modules loaded)", module.__name__, len(sys.modules))
            else:
                self.attach_app(subOptions)
