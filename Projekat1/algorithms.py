import struct
from math import log2

from bitstream import BitReader, BitWriter

SHANNON_FANO_FILE_ID = b"SF01"
HUFFMAN_FILE_ID = b"HF01"


def byte_entropy(data):
    if len(data) == 0:
        return 0.0

    counts = [0] * 256

    for byte in data:
        counts[byte] += 1

    entropy = 0.0
    data_size = len(data)

    for count in counts:
        if count > 0:
            probability = count / data_size
            entropy -= probability * log2(probability)

    return entropy


def byte_counts(data):
    counts = [0] * 256

    for byte in data:
        counts[byte] += 1

    return counts


def shannon_fano_codes(counts):
    symbols = []

    for byte, count in enumerate(counts):
        if count > 0:
            symbols.append((byte, count))

    symbols.sort(key=lambda item: (-item[1], item[0]))
    codes = {}

    def divide(group, prefix):
        if len(group) == 1:
            codes[group[0][0]] = prefix or "0"
            return

        total = sum(item[1] for item in group)
        left_sum = 0
        best_split = 1
        best_difference = total

        for split in range(1, len(group)):
            left_sum += group[split - 1][1]
            difference = abs(total - 2 * left_sum)

            if difference < best_difference:
                best_difference = difference
                best_split = split

        divide(group[:best_split], prefix + "0")
        divide(group[best_split:], prefix + "1")

    if symbols:
        divide(symbols, "")

    return codes


def huffman_codes(counts):
    nodes = []

    for byte, count in enumerate(counts):
        if count > 0:
            nodes.append((count, byte, byte))

    if not nodes:
        return {}

    if len(nodes) == 1:
        byte = nodes[0][2]
        return {byte: "0"}

    next_order = 256

    while len(nodes) > 1:
        nodes.sort(key=lambda item: (item[0], item[1]))
        first_count, _, first_node = nodes.pop(0)
        second_count, _, second_node = nodes.pop(0)
        node = (first_node, second_node)
        nodes.append((first_count + second_count, next_order, node))
        next_order += 1

    root = nodes[0][2]
    codes = {}

    def visit(node, prefix):
        if isinstance(node, int):
            codes[node] = prefix
            return

        left, right = node
        visit(left, prefix + "0")
        visit(right, prefix + "1")

    visit(root, "")
    return codes


def encode_with_prefix_code(data, codes, file_id):
    header = bytearray(file_id)
    header.extend(struct.pack("<QH", len(data), len(codes)))

    for byte in sorted(codes):
        code = codes[byte]
        code_value = int(code, 2)
        code_bytes = code_value.to_bytes((len(code) + 7) // 8, "big")
        header.extend(struct.pack("BB", byte, len(code)))
        header.extend(code_bytes)

    writer = BitWriter()

    for byte in data:
        writer.write_code(codes[byte])

    return bytes(header) + writer.finish()


def decode_prefix_code(encoded, expected_file_id):
    if len(encoded) < 14 or encoded[:4] != expected_file_id:
        raise ValueError("Invalid compressed file header")

    original_size, symbol_count = struct.unpack("<QH", encoded[4:14])
    position = 14
    root = {}

    for _ in range(symbol_count):
        if position + 2 > len(encoded):
            raise ValueError("Incomplete code table")

        byte, code_length = struct.unpack("BB", encoded[position:position + 2])
        position += 2
        stored_size = (code_length + 7) // 8

        if code_length == 0 or position + stored_size > len(encoded):
            raise ValueError("Invalid code table")

        code_value = int.from_bytes(encoded[position:position + stored_size], "big")
        position += stored_size
        node = root

        for bit_position in range(code_length - 1, -1, -1):
            bit = (code_value >> bit_position) & 1
            node = node.setdefault(bit, {})

        if "byte" in node:
            raise ValueError("Duplicate code in code table")

        node["byte"] = byte

    if original_size == 0:
        return b""

    reader = BitReader(encoded[position:])
    result = bytearray()

    while len(result) < original_size:
        node = root

        while "byte" not in node:
            bit = reader.read_bit()

            if bit not in node:
                raise ValueError("Compressed data does not match the code table")

            node = node[bit]

        result.append(node["byte"])

    return bytes(result)


def shannon_fano_compress(data):
    codes = shannon_fano_codes(byte_counts(data))
    return encode_with_prefix_code(data, codes, SHANNON_FANO_FILE_ID)


def shannon_fano_decompress(encoded):
    return decode_prefix_code(encoded, SHANNON_FANO_FILE_ID)


def huffman_compress(data):
    codes = huffman_codes(byte_counts(data))
    return encode_with_prefix_code(data, codes, HUFFMAN_FILE_ID)


def huffman_decompress(encoded):
    return decode_prefix_code(encoded, HUFFMAN_FILE_ID)
