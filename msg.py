""" This module contains classes for the message structure used by the
server and client to communicate. It also contains shared functions
used by both the server and client. """
import struct


class Header:
    def __init__(self, size: int, qid: int):
        self.size = size
        self.qid = qid

    def encode(self):
        # pack struct with uint16
        ba = bytearray()
        ba.extend(struct.pack('<H', self.size))
        ba.extend(struct.pack('<H', self.qid))
        return bytes(ba)

    @staticmethod
    def decode(data):
        # unpack struct with uint16
        size = struct.unpack_from('<H', data, 0)[0]
        qid = struct.unpack_from('<H', data, 2)[0]
        return Header(size, qid)


class VarLength:
    """ A message with variable length payload. Parent class for the 
    Question and ResourceRecord classes. """

    def __init__(self, str_type: str, payload: str):
        self.str_type = str_type
        self.payload = payload

    def _encode(self, type_to_id):
        ba = bytearray()
        # pack struct with uint16
        ba.extend(struct.pack('<H', len(self.payload)))
        ba.extend(struct.pack('<H', type_to_id[self.str_type]))
        # pack struct with variable length string
        ba.extend(struct.pack(f'<{len(self.payload)}s', self.payload.encode()))
        return bytes(ba)

    @staticmethod
    def _decode_header(data, id_to_type):
        # unpack struct with uint16
        size = struct.unpack_from('<H', data, 0)[0]
        type_id = struct.unpack_from('<H', data, 2)[0]
        return size, id_to_type[type_id]

    @staticmethod
    def decode_payload(size, data):
        # unpack struct with variable length string
        payload = struct.unpack_from(f'<{size}s', data, 0)[0]
        return payload.decode()


class Question(VarLength):
    def __init__(self, str_type: str, payload: str):
        super().__init__(str_type, payload)

    def encode(self):
        # call parent method with question type -> id mapping
        return self._encode({"A": 1, "NS": 2, "CNAME": 5})

    @staticmethod
    def decode_header(data):
        # call parent method with id -> question type mapping
        return super(Question, Question)._decode_header(
            data, {1: "A", 2: "NS", 5: "CNAME"})


class ResourceRecord(VarLength):
    def __init__(self, str_type: str, payload: str):
        super().__init__(str_type, payload)

    def encode(self):
        # call parent method with resource type -> id mapping
        return self._encode({"Answer": 1, "Authority": 2, "Additional": 3})

    @staticmethod
    def decode_header(data):
        # call parent method with id -> resource type mapping
        return super(ResourceRecord, ResourceRecord)._decode_header(
            data, {1: "Answer", 2: "Authority", 3: "Additional"})


def decode_request(data):
    # decode header
    header = Header.decode(data[:4])
    # decode header of variable length segment
    qsize, qtype = Question.decode_header(data[4:8])
    # decode payload of variable length segment
    qname = Question.decode_payload(qsize, data[8:8 + qsize])
    return header, Question(qtype, qname)


def decode_response(data):
    # pointer for how many bytes have been read
    cur = 0

    # decode header
    header = Header.decode(data[cur:cur + 4])
    cur += 4

    # decode question
    qsize, qtype = Question.decode_header(data[cur:cur + 4])
    cur += 4
    qname = Question.decode_payload(qsize, data[cur:cur + qsize])
    cur += qsize
    question = Question(qtype, qname)

    rrs = []
    for i in range(3):
        if header.size == cur - 4:
            # no more resource records
            return header, question, rrs
        # decode resource record
        rsize, rtype = ResourceRecord.decode_header(data[cur:cur + 4])
        cur += 4
        records = ResourceRecord.decode_payload(rsize, data[cur:cur + rsize])
        cur += rsize
        rrs.append(ResourceRecord(rtype, records))

    return header, question, rrs
