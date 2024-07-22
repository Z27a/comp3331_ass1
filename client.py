import random
import sys
import socket

from msg import *


def make_request(qname: str, qtype: str):
    # create question
    question = Question(qtype, qname).encode()

    # create header
    qid = random.randrange(65535)
    header = Header(len(question), qid).encode()

    # create byets object
    ba = bytearray()
    ba.extend(header)
    ba.extend(question)
    return bytes(ba), qid


def client(server_port, qname, qtype, timeout):
    data, qid = make_request(qname, qtype)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        print(f"QID: {qid}\n")
        print("QUESTION SECTION:")
        print(qname, qtype, "\n")

        # send data
        sock.settimeout(timeout)
        sock.sendto(data, ("localhost", server_port))

        try:
            # receive data
            res, _ = sock.recvfrom(2048)
            header, question, rrs = decode_response(res)

            for rr in rrs:
                print(f"{rr.str_type.upper()} SECTION:")
                print(rr.payload)

        except socket.timeout:
            print(f"ERR: socket timed out after {timeout} seconds")


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('Usage: client.py <server_port> <qname> <qtype> <timeout>')
        exit(1)

    client(int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]))
