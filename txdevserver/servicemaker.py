from twisted.python import usage
from txdevserver.service import DevServer
from twisted.web import server
from twisted.application import internet


class Options(usage.Options):
    def __init__(self):
        super(Options, self).__init__()
        self['static'] = {}
        self['resources'] = {}

    def opt_resource(self, res):
        """Add a twisted Resource under the path using a -r path=resource.object format"""
        url_part, _sep, import_name = res.partition('=')
        self['resources'][url_part] = import_name

    opt_r = opt_resource

    def opt_staticdir(self, staticdir):
        """Add a static dir, in -s static/ or -s static_url=static/directory/ format"""
        if '=' in staticdir:
            url_part, _sep, static_path = staticdir.partition('=')
        else:
            url_part = static_path = staticdir

        self['static'][url_part] = static_path

    opt_s = opt_staticdir

    def parseArgs(self, app=None):
        self['app'] = app


def makeService(subOptions):
    root = DevServer(subOptions)

    site = server.Site(root)
    srv = internet.TCPServer(8000, site)
    return srv
