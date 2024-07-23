import datetime
import random
import sys
import socket
import time
import threading

from msg import *


def make_response(header, question, ans, auth, add):
    question = question.encode()
    size = len(question)

    # encode resource records
    if ans != "":
        ans = ResourceRecord("Answer", ans).encode()
        size += len(ans)
    if auth != "":
        auth = ResourceRecord("Authority", auth).encode()
        size += len(auth)
    if add != "":
        add = ResourceRecord("Additional", add).encode()
        size += len(add)

    # create byte object
    ba = bytearray()
    ba.extend(Header(size, header.qid).encode())
    ba.extend(question)
    if ans != "":
        ba.extend(ans)
    if auth != "":
        ba.extend(auth)
    if add != "":
        ba.extend(add)

    return bytes(ba)


class Server:
    def __init__(self, server_port):
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.server_port))
        self.addr = {}
        self.cname = {}
        self.ns = {}

        with open("master.txt") as f:
            lines = f.read().split("\n")
            # process master file
            for line in lines:
                line = line.split()
                domain_name, rtype, data = line[0], line[1], line[2]
                if rtype == "A":
                    if domain_name in self.addr:
                        self.addr[domain_name].add(data)
                    else:
                        self.addr[domain_name] = {data}
                elif rtype == "CNAME":
                    if domain_name in self.cname:
                        print(f"WARN: multiple CNAME entries found for {domain_name} in master file")
                    self.cname[domain_name] = data
                elif rtype == "NS":
                    if domain_name in self.ns:
                        self.ns[domain_name].add(data)
                    else:
                        self.ns[domain_name] = {data}
                else:
                    print("ERR: Record type mismatch in master file!")

    def run(self):
        print(f'Server running on localhost:{self.server_port}...')

        while True:
            try:
                # receive data
                data, addr = self.sock.recvfrom(2048)
                header, question = decode_request(data)
                # delegate processing to thread
                child = threading.Thread(target=self.process_request, args=(header, question, addr))
                child.start()

            except ConnectionResetError:
                print(f"WARN: Connection closed by {addr[1]}")

    def process_request(self, header, question, addr):
        # sleep the thread
        delay = random.randrange(5)
        print(f"{datetime.datetime.now()} rcv {addr[1]}: {header.qid} {
                question.payload} {question.str_type} (delay: {delay}s)")
        time.sleep(delay)

        # get resource records and make response
        ans_str, auths_str, adds_str = self.find_record(question.str_type, question.payload)
        response = make_response(header, question, ans_str, auths_str, adds_str)

        # send response
        print(f"{datetime.datetime.now()} snd {addr[1]}: {header.qid} {question.payload} {question.str_type}")
        self.sock.sendto(response, addr)

    def find_record(self, qtype, qname, ans_str="", auths_str="", adds_str=""):
        if qtype == "CNAME" and qname in self.cname:
            # direct match CNAME
            ans_str += f"{qname} CNAME {self.cname[qname]}\n"
        elif qtype == "A" and qname in self.addr:
            # direct match A
            for val in self.addr[qname]:
                ans_str += f"{qname} A {val}\n"
        elif qtype == "NS" and qname in self.ns:
            # direct match NS
            for val in self.ns[qname]:
                ans_str += f"{qname} NS {val}\n"
        elif qtype != "CNAME" and qname in self.cname:
            # indirect match, recurse with CNAME
            ans_str += f"{qname} CNAME {self.cname[qname]}\n"
            return self.find_record(qtype, self.cname[qname], ans_str, auths_str, adds_str)
        else:
            # no match, find the closest ancestor zone
            sections = qname.split(".")
            sections.pop(0)
            if len(sections) == 1:
                ancestor = "."
            else:
                ancestor = ".".join(sections)
            while ancestor not in self.ns:
                sections.pop(0)
                if len(sections) == 1:
                    ancestor = "."
                else:
                    ancestor = ".".join(sections)

            # add values to authority and additional section
            for val in self.ns[ancestor]:
                auths_str += f"{ancestor} NS {val}\n"
                if val in self.addr:
                    for addr in self.addr[val]:
                        adds_str += f"{val} A {addr}\n"

        return ans_str, auths_str, adds_str


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: server.py <server_port>')
        exit(1)

    server = Server(int(sys.argv[1]))
    try:
        server.run()
    except KeyboardInterrupt:
        exit(0)
