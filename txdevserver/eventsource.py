import json
from functools import partial
from collections import deque


from twisted.web.resource import Resource
from twisted.web import server


class EventSource(Resource):
    _sent = deque([], maxlen=30)
    clients = []
    id = 0

    def send_event(self, request, event, data, inc=True):
        message = json.dumps({"event": event, "data": data})
        request.write('id: %s\ndata: %s\n\n' % (self.id, message))
        if inc:
            self.id += 1
            self._sent.appendleft((self.id, event, data))

    def send_to_all(self, event, data, inc=True):
        for client in self.clients:
            self.send_event(client, event, data, inc=False)
        if inc:
            self.id += 1
            self._sent.appendleft((self.id, event, data))

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        request.setResponseCode(200)
        request.setHeader('Content-Type', 'text/event-stream')

        request.notifyFinish().addErrback(partial(self.close_es_request, request=request))

        self.clients.append(request)
        self.send_event(request, "hello", "null", inc=False)

        # self.send_old_events(request, last_event_id, count=10)

        return server.NOT_DONE_YET

    def send_old_events(self, request, last_id, count=10):
        for num, (current_id, event, data) in enumerate(self._sent):
            if num > count or current_id <= last_id:
                break
            self.send_event(request, event, data, inc=False)

    def close_es_request(self, error=None, request=None):

        self.clients.remove(request)

