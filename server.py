import datetime
import sys
import socket
import time

from msg import *


class Server:
    def __init__(self, server_port):
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.server_port))

    def run(self):
        print(f'Server running on localhost:{self.server_port}...')

        while True:
            data, addr = self.sock.recvfrom(1024)
            header, question = decode_request(data)
            self.process_request(header, question, addr)

            # child = threading.Thread(target=self._process_request, args=(data, addr))
            # child.start()

    def process_request(self, header, question, addr):
        rcv_time = datetime.datetime.now()
        delay = random.randrange(5)
        print(f"{rcv_time} rcv {addr[1]}: {header.qid} {question.qname} {question.qtype} (delay: {delay}s)")

        time.sleep(delay)

        ans, auths, adds = self.find_resource_records()
        response = self.make_response(header, question, ans, auths, adds)

        self.sock.sendto(response, addr)

    def find_resource_records(self):
        ans = ResourceRecord("Answer", "A | 192.31.80.30")
        auths = ResourceRecord("Authority", "CNAME | bar.example.com.")
        adds = ResourceRecord("Additional", "NS | b.root-servers.net.")
        return ans, auths, adds

    def make_response(self, header, question, ans, auth, add):
        question = question.encode()
        size = len(question)

        if ans is not None:  # can this really be none?
            ans = ans.encode()
            size += len(ans)
        if auth is not None:
            auth = auth.encode()
            size += len(auth)
        if add is not None:
            add = add.encode()
            size += len(add)

        ba = bytearray()
        ba.extend(Header(size, header.qid).encode())
        ba.extend(question)
        if ans is not None:  # can this really be none?
            ba.extend(ans)
        if auth is not None:
            ba.extend(auth)
        if add is not None:
            ba.extend(add)

        return bytes(ba)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: server.py <server_port>')
        exit(1)

    server = Server(int(sys.argv[1]))
    try:
        server.run()
    except KeyboardInterrupt:
        exit(0)
