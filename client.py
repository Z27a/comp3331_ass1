import sys
import socket

from msg import *

def client(server_port, qname, qtype, timeout):
    data, qid = make_query(qname, qtype)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        print(f"Sending request to {server_port}, qid: {qid}")
        sock.sendto(data, ("localhost", server_port))

        try:
            res, _ = sock.recvfrom(1024)
            header, question = decode_query(res)
            print(header.qid)

        except socket.timeout:
            print(f"ERR: socket timed out after {timeout} seconds")


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('Usage: client.py <server_port> <qname> <qtype> <timeout>')
        exit(1)

    client(int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]))
