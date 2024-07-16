import struct
import random

QTYPE_TO_ID = {"A": 1, "NS": 2, "CNAME": 5}
ID_TO_QTYPE = {1: "A", 2: "NS", 5: "CNAME"}
RTYPE_TO_ID = {"Answer": 1, "Authority": 2, "Additional": 3}
ID_TO_RTYPE = {1: "Answer", 2: "Authority", 3: "Additional"}


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

    def encode(self):
        ba = bytearray()
        ba.extend(struct.pack('<H', len(self.records)))
        ba.extend(struct.pack('<H', RTYPE_TO_ID[self.rtype]))
        ba.extend(struct.pack(f'<{len(self.records)}s', self.records.encode()))
        return bytes(ba)

    @staticmethod
    def decode_header(data):
        size = struct.unpack_from('<H', data, 0)[0]
        rtype_id = struct.unpack_from('<H', data, 2)[0]
        return size, ID_TO_RTYPE[rtype_id]

    @staticmethod
    def decode_record(size, data):
        records = struct.unpack_from(f'<{size}s', data, 0)[0]
        return records.decode()


def decode_request(data):
    header = Header.decode(data[:4])
    qsize, qtype = Question.decode_header(data[4:8])
    qname = Question.decode_qname(qsize, data[8:8 + qsize])
    return header, Question(qtype, qname)


def decode_response(data):
    cur = 0

    # header
    header = Header.decode(data[cur:cur + 4])
    cur += 4

    # question
    qsize, qtype = Question.decode_header(data[cur:cur + 4])
    cur += 4
    qname = Question.decode_qname(qsize, data[cur:cur + qsize])
    cur += qsize
    question = Question(qtype, qname)

    rrs = []

    for i in range(3):
        if header.size == cur - 4:
            return header, question, rrs

        # resource record
        rsize, rtype = ResourceRecord.decode_header(data[cur:cur + 4])
        cur += 4
        records = ResourceRecord.decode_record(rsize, data[cur:cur + rsize])
        cur += rsize
        rrs.append(ResourceRecord(rtype, records))

    if header.size != cur - 4:
        print("ERR: header size mismatch when decoding response")

    return header, question, rrs
