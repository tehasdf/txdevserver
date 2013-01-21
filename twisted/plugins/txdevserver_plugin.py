from zope.interface import implements
from twisted.application import service, internet
from twisted.plugin import IPlugin
from txdevserver import importer
from txdevserver.runner import sigil
from txdevserver.loggers import ESLogger
from functools import partial
import time
from twisted.web import server
from twisted.web.resource import Resource
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from twisted.python import usage
from twisted.web.static import File
from txdevserver.loggers import log_request


class LoggedWSGIResource(WSGIResource):
    def __init__(self, reactor, threadPool, app, additional_log_params=None):
        super(LoggedWSGIResource, self).__init__(reactor, threadPool, app)
        if additional_log_params:
            self.additional_log_params = additional_log_params

    def render(self, request):
        additional_log_params = self.additional_log_params()
        request.notifyFinish().addCallback(partial(log_request, request=request, 
            start_time=time.time(), params_factory=additional_log_params))
        return super(LoggedWSGIResource, self).render(request)

class Root(Resource, object):
    def __init__(self, app):
        super(Root, self).__init__()

        self.app = app

    def getChild(self, path, request):
        request.postpath.insert(0, request.prepath.pop(0))
        return self.app

class AppGetter(str, object):
    _name = "txdevserver"
    def __init__(self, parent):
        self.parent = parent

    def __eq__(self, other):
        if other is sigil:
            self._name = '...'
            self.parent.app = sigil
            return True
        try:
            app = importer.import_string(other)
        except ImportError:
            return False
        else:
            self.parent.app = app
            self._name = other
            return True

    def __len__(self):
        return len(self._name)

    def __str__(self):
        return self._name

    def __add__(self, other):
        return 'foo'
    def __radd__(self, other):
        return 'bar'

class WebappOptions(usage.Options):
    def __init__(self):
        super(WebappOptions, self).__init__()
        self['static'] = {}
        self['resources'] = {}

    def opt_staticdir(self, staticdir):
        """Add a static dir, in -s static/ or -s static_url=static/directory/ format"""
        if '=' in staticdir:
            url_part, _sep, static_path = staticdir.partition('=')
        else:
            url_part = static_path = staticdir

        self['static'][url_part] = static_path

    opt_s = opt_staticdir

    def opt_resource(self, res):
        """Add a twisted Resource under the path using a -r path=resource.object format"""
        url_part, _sep, import_name = res.partition('=')
        try:
            resource_to_add = importer.import_string(import_name)
        except ImportError:
            return
        else:
            self['resources'][url_part] = resource_to_add

    opt_r = opt_resource

    def postOptions(self):
        if self.parent.defaultSubCommand is sigil:
            self.update(self.parent.appOpts)

class _WebappServiceMaker(object):
    implements(IPlugin, service.IServiceMaker)
    _appGetter = None
    description = "Put your webapp's import name here, like mypackage.mymodule.application"
    options = WebappOptions

    @property
    def tapname(self):
        if self._appGetter is None:
            self._appGetter = AppGetter(self)
        return self._appGetter

    def makeService(self, subOptions):
        if self.app is sigil:
            self.app = subOptions['app']

        wsgi_resource = LoggedWSGIResource(reactor, reactor.getThreadPool(), self.app, 
            subOptions.get('log_data_factory'))
        root = Root(wsgi_resource)

        for url_part, static_path in subOptions['static'].iteritems():
            static_resource = File(static_path)
            root.putChild(url_part, static_resource)

        for url_part, resource in subOptions['resources'].iteritems():
            root.putChild(url_part, resource)

        logger_static = File(subOptions['logger_file'])

        root.putChild("log", logger_static)
        root.putChild("log_es", ESLogger)

        site = server.Site(root)
        srv = internet.TCPServer(8000, site)
        return srv


WebappServiceMaker = _WebappServiceMaker()

