import socket
import threading

from httpy import handler

class Thread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        kwargs["thread"] = self

        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs)

class HTTP:
    _version = "0.0.1"

    def __init__(self, host, port, handle=handler.Handle, sock_family=socket.AF_INET, sock_type=socket.SOCK_STREAM):
        self.host = host
        self.port = port
        self.binded = False

        self.family = sock_family
        self.type = sock_type
        self.handle = handle
        self.socket = socket.socket(sock_family, sock_type)
        self.threads = []

        self.stop_loop = False
        self.stopped = True

    def send_data(self, conn, data):
        self.send_data_raw(conn, data.encode())

    def send_data_raw(self, conn, data, ending=True):
        conn.send(data + b'\r\n' if ending else data)

    def get_data(self, conn):
        data = conn.recv(1024)

        if not data:
            return None

        return data.decode().split("\n")

    def interp_request(self, conn, addr, thread=None):
        if thread != None:
            self.threads.append(thread)

        method = "GET"
        path = "/"
        request_protocal = "HTTP/1.0"
        headers = {}
        body = ""

        section = 0
        part_start = None

        length = 0
        data = self.get_data(conn)

        while data is not None:
            while True:
                if section != 2:
                    part = data.pop(0)

                    if not part.endswith("\r"):
                        part_start = part
                        break

                    part = part[:-1]

                    if section == 0:
                        method, path, request_protocal = part.split(" ")
                        section = 1
                        continue

                    elif section == 1:
                        if part == "":
                            section = 2
                            continue

                        name, value = part.split(": ")
                        headers[name] = value
                        continue

                elif not "Content-Length" in headers or int(headers["Content-Length"]) == 0:
                    break
                else:
                    body += "\n".join(data)

                    if len(body) == int(headers["Content-Length"]):
                        break

            if section == 2:
                if not "Content-Length" in headers or int(headers["Content-Length"]) == 0:
                    break
                elif int(headers["Content-Length"]) == len(body):
                    break

            data = self.get_data(conn)
            if part_start is not None:
                parts[0] = part_start + parts[0]
                part_start = None

        handler = self.handle(self, conn, addr, method=method, path=path, request_protocal=request_protocal, headers=headers, body=body, thread=thread)
        handler.handle()

    def end_interp_request(self, conn, addr, thread=None):
        conn.close()

        if thread != None:
            self.threads.remove(thread)

    def _stop(self):
        if not self.stopped:  # Force while loop to continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))

    def stop(self):
        self.stop_loop = True

        thread = threading.Thread(target=self._stop)
        thread.daemon = True
        thread.start()

    def listen(self, threaded_conns=False):
        if not self.binded:
            self.socket.bind((self.host, self.port))
            self.binded = True
            self.stopped = False

            self.socket.listen(6)
            while not self.stop_loop:
                conn, addr = self.socket.accept()
                if threaded_conns:
                    thread = Thread(target=self.interp_request, args=(conn, addr))
                    thread.daemon = True
                    thread.start()
                else:
                    self.interp_request(conn, addr)

        self.stopped = True
