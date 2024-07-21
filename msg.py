import struct
import random


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


class VarLength:
    def __init__(self, str_type: str, payload: str):
        self.str_type = str_type
        self.payload = payload

    def _encode(self, type_to_id):
        ba = bytearray()
        ba.extend(struct.pack('<H', len(self.payload)))
        ba.extend(struct.pack('<H', type_to_id[self.str_type]))
        ba.extend(struct.pack(f'<{len(self.payload)}s', self.payload.encode()))
        return bytes(ba)

    @staticmethod
    def _decode_header(data, id_to_type):
        size = struct.unpack_from('<H', data, 0)[0]
        type_id = struct.unpack_from('<H', data, 2)[0]
        return size, id_to_type[type_id]

    @staticmethod
    def decode_payload(size, data):
        payload = struct.unpack_from(f'<{size}s', data, 0)[0]
        return payload.decode()


class Question(VarLength):
    def __init__(self, str_type: str, payload: str):
        super().__init__(str_type, payload)

    def encode(self):
        return self._encode({"A": 1, "NS": 2, "CNAME": 5})

    @staticmethod
    def decode_header(data):
        return super(Question, Question)._decode_header(data, {1: "A", 2: "NS", 5: "CNAME"})


class ResourceRecord(VarLength):
    def __init__(self, str_type: str, payload: str):
        super().__init__(str_type, payload)

    def encode(self):
        return self._encode({"Answer": 1, "Authority": 2, "Additional": 3})

    @staticmethod
    def decode_header(data):
        return super(ResourceRecord, ResourceRecord)._decode_header(
            data, {1: "Answer", 2: "Authority", 3: "Additional"})


# class Question:
#     def __init__(self, qtype: str, qname: str):
#         self.qtype = qtype
#         self.qname = qname
#
#     def encode(self):
#         ba = bytearray()
#         ba.extend(struct.pack('<H', len(self.qname)))
#         ba.extend(struct.pack('<H', QTYPE_TO_ID[self.qtype]))
#         ba.extend(struct.pack(f'<{len(self.qname)}s', self.qname.encode()))
#         return bytes(ba)
#
#     @staticmethod
#     def decode_header(data):
#         size = struct.unpack_from('<H', data, 0)[0]
#         qtype_id = struct.unpack_from('<H', data, 2)[0]
#         return size, ID_TO_QTYPE[qtype_id]
#
#     @staticmethod
#     def decode_qname(size, data):
#         qname = struct.unpack_from(f'<{size}s', data, 0)[0]
#         return qname.decode()


# class ResourceRecord:
#     def __init__(self, rtype: str, records: str):
#         self.rtype = rtype
#         self.records = records
#
#     def encode(self):
#         ba = bytearray()
#         ba.extend(struct.pack('<H', len(self.records)))
#         ba.extend(struct.pack('<H', RTYPE_TO_ID[self.rtype]))
#         ba.extend(struct.pack(f'<{len(self.records)}s', self.records.encode()))
#         return bytes(ba)
#
#     @staticmethod
#     def decode_header(data):
#         size = struct.unpack_from('<H', data, 0)[0]
#         rtype_id = struct.unpack_from('<H', data, 2)[0]
#         return size, ID_TO_RTYPE[rtype_id]
#
#     @staticmethod
#     def decode_record(size, data):
#         records = struct.unpack_from(f'<{size}s', data, 0)[0]
#         return records.decode()

def make_request(qname: str, qtype: str):
    question = Question(qtype, qname).encode()
    qid = random.randrange(65535)
    header = Header(len(question), qid).encode()

    ba = bytearray()
    ba.extend(header)
    ba.extend(question)
    return bytes(ba), qid


def decode_request(data):
    header = Header.decode(data[:4])
    qsize, qtype = Question.decode_header(data[4:8])
    qname = Question.decode_payload(qsize, data[8:8 + qsize])
    return header, Question(qtype, qname)


def decode_response(data):
    cur = 0

    # header
    header = Header.decode(data[cur:cur + 4])
    cur += 4

    # question
    qsize, qtype = Question.decode_header(data[cur:cur + 4])
    cur += 4
    qname = Question.decode_payload(qsize, data[cur:cur + qsize])
    cur += qsize
    question = Question(qtype, qname)

    rrs = []

    for i in range(3):
        if header.size == cur - 4:
            return header, question, rrs

        # resource record
        rsize, rtype = ResourceRecord.decode_header(data[cur:cur + 4])
        cur += 4
        records = ResourceRecord.decode_payload(rsize, data[cur:cur + rsize])
        cur += rsize
        rrs.append(ResourceRecord(rtype, records))

    if header.size != cur - 4:
        print("ERR: header size mismatch when decoding response")

    return header, question, rrs
