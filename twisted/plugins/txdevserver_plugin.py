from twisted.application.service import ServiceMaker

serviceMaker = ServiceMaker('txdevserver', 'txdevserver.servicemaker',
    "Put your webapp's import name here, like mypackage.mymodule.application", 'txdevserver')
