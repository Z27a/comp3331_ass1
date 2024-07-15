import struct
import random

QTYPE_TO_ID = {"A": 1, "NS": 2, "CNAME": 5}
ID_TO_QTYPE = {1: "A", 2: "NS", 5: "CNAME"}
RTYPE_TO_ID = {"answer": 1, "authority": 2, "additional": 3}
ID_TO_RTYPE = {1: "answer", 2: "authority", 3: "additional"}


class Header:
    def __init__(self, size: int, qid: int):
        self.size = size
        self.qid = qid

    def encode(self):
        ba = bytearray()
        # size - unsigned short
        ba.extend(struct.pack('<H', self.size))
        # qid - unsigned short
        ba.extend(struct.pack('<H', self.qid))
        return bytes(ba)

    @staticmethod
    def decode(data):
        size = struct.unpack_from('<H', data, 0)[0]
        qid = struct.unpack_from('<H', data, 2)[0]
        return Header(size, qid)


class Question:
    def __init__(self, qtype: str, qname: str):
        self.qtype = qtype
        self.qname = qname

    def encode(self):
        ba = bytearray()
        ba.extend(struct.pack('<H', len(self.qname)))
        ba.extend(struct.pack('<H', QTYPE_TO_ID[self.qtype]))
        ba.extend(struct.pack(f'<{len(self.qname)}s', self.qname.encode()))
        return bytes(ba)

    @staticmethod
    def decode_header(data):
        size = struct.unpack_from('<H', data, 0)[0]
        qtype_id = struct.unpack_from('<H', data, 2)[0]
        return size, ID_TO_QTYPE[qtype_id]

    @staticmethod
    def decode_qname(size, data):
        qname = struct.unpack_from(f'<{size}s', data, 0)[0]
        return qname.decode()


class ResourceRecord:
    def __init__(self, rtype: str, records: str):
        self.rtype = rtype
        self.records = records

    def to_bytes(self):
        ba = bytearray()
        ba.extend(struct.pack('<H', len(self.records)))
        ba.extend(struct.pack('<H', RTYPE_TO_ID[self.rtype]))
        ba.extend(struct.pack(f'<{len(self.records)}s', self.records))
        return bytes(ba)

    @staticmethod
    def from_bytes(data):
        size = struct.unpack_from('<H', data, 0)[0]
        rtype_id = struct.unpack_from('<H', data, 2)[0]
        records = struct.unpack_from(f'<{size}s', data, 4)[0]
        return Question(ID_TO_RTYPE[rtype_id], records)

def make_query(qname: str, qtype: str):
    question = Question(qtype, qname).encode()
    qid = random.randrange(65535)
    header = Header(len(question), qid).encode()

    ba = bytearray()
    ba.extend(header)
    ba.extend(question)
    return bytes(ba), qid

def decode_query(data):
    header = Header.decode(data[:4])
    qsize, qtype = Question.decode_header(data[4:8])
    qname = Question.decode_qname(qsize, data[8:8 + qsize])
    return header, Question(qtype, qname)
