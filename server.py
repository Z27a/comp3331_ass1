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
            header, question = decode_query(data)
            self.process_request(header, question, addr)

            # child = threading.Thread(target=self._process_request, args=(data, addr))
            # child.start()

    def process_request(self, header, question, addr):
        rcv_time = datetime.datetime.now()
        delay = random.randrange(5)
        print(f"{rcv_time} rcv {addr[1]}: {header.qid} {question.qname} {question.qtype} (delay: {delay}s)")

        time.sleep(delay)

        response, _ = make_query(question.qname, question.qtype)

        self.sock.sendto(response, addr)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: server.py <server_port>')
        exit(1)

    server = Server(int(sys.argv[1]))
    try:
        server.run()
    except KeyboardInterrupt:
        exit(0)

