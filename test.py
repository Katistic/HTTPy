import httpy
from httpy.handler import Handle

class Handler(Handle):
    def on_GET(self):
        print("Get request at %s" % self.path)

        self.send_response_only(405)

server = httpy.HTTP('', 8080, handle=Handler)
server.listen()
