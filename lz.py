import struct
from collections import deque

from bitstream import BitReader, BitWriter


LZ77_FILE_ID = b"LZ77"
LZW_FILE_ID = b"LZW1"


def find_lz77_match(data, position, window_size, max_length,
                    three_byte_positions, last_two, last_one):
    remaining = min(max_length, len(data) - position)
    best_distance = 0
    best_length = 0

    if remaining >= 3:
        key = data[position:position + 3]

        for candidate in reversed(three_byte_positions.get(key, ())):
            length = 3

            while (length < remaining and
                   data[candidate + length] == data[position + length]):
                length += 1

            if length > best_length:
                best_distance = position - candidate
                best_length = length

            if best_length == remaining:
                break

    if best_length == 0 and remaining >= 2:
        candidate = last_two.get(data[position:position + 2])

        if candidate is not None and position - candidate <= window_size:
            best_distance = position - candidate
            best_length = 2

    if best_length == 0:
        candidate = last_one[data[position]]

        if candidate >= 0 and position - candidate <= window_size:
            best_distance = position - candidate
            best_length = 1

    return best_distance, best_length


def add_lz77_position(data, position, window_size,
                      three_byte_positions, last_two, last_one):
    old_position = position - window_size

    if old_position >= 0 and old_position + 2 < len(data):
        old_key = data[old_position:old_position + 3]
        positions = three_byte_positions.get(old_key)

        if positions and positions[0] == old_position:
            positions.popleft()

            if not positions:
                del three_byte_positions[old_key]

    if position + 2 < len(data):
        key = data[position:position + 3]
        three_byte_positions.setdefault(key, deque()).append(position)

    if position + 1 < len(data):
        last_two[data[position:position + 2]] = position

    last_one[data[position]] = position


def lz77_compress(data, window_size=4096, max_length=255):
    if not 1 <= window_size <= 65535:
        raise ValueError("Window size must be between 1 and 65535")

    if not 1 <= max_length <= 65535:
        raise ValueError("Maximum match length must be between 1 and 65535")

    header = LZ77_FILE_ID + struct.pack(
        "<QHH", len(data), window_size, max_length
    )
    writer = BitWriter()
    distance_bits = (window_size - 1).bit_length()
    length_bits = (max_length - 1).bit_length()
    three_byte_positions = {}
    last_two = {}
    last_one = [-1] * 256
    position = 0

    while position < len(data):
        distance, length = find_lz77_match(
            data,
            position,
            window_size,
            max_length,
            three_byte_positions,
            last_two,
            last_one,
        )

        if length == 0:
            writer.write_bit(0)
            writer.write_bits(data[position], 8)
            consumed = 1
        else:
            writer.write_bit(1)
            writer.write_bits(distance - 1, distance_bits)
            writer.write_bits(length - 1, length_bits)
            consumed = length

        for current in range(position, position + consumed):
            add_lz77_position(
                data,
                current,
                window_size,
                three_byte_positions,
                last_two,
                last_one,
            )

        position += consumed

    return header + writer.finish()


def lz77_decompress(encoded):
    if len(encoded) < 16 or encoded[:4] != LZ77_FILE_ID:
        raise ValueError("Invalid LZ77 file header")

    original_size, window_size, max_length = struct.unpack(
        "<QHH", encoded[4:16]
    )

    if window_size == 0 or max_length == 0:
        raise ValueError("Invalid LZ77 parameters")

    reader = BitReader(encoded[16:])
    distance_bits = (window_size - 1).bit_length()
    length_bits = (max_length - 1).bit_length()
    result = bytearray()

    while len(result) < original_size:
        token_type = reader.read_bit()

        if token_type == 0:
            result.append(reader.read_bits(8))
            continue

        distance = reader.read_bits(distance_bits) + 1
        length = reader.read_bits(length_bits) + 1

        if distance > window_size or distance > len(result):
            raise ValueError("Invalid LZ77 distance")

        if length > max_length or len(result) + length > original_size:
            raise ValueError("Invalid LZ77 match length")

        for _ in range(length):
            result.append(result[-distance])

    return bytes(result)


def lzw_compress(data, code_width=12):
    if not 9 <= code_width <= 16:
        raise ValueError("LZW code width must be between 9 and 16 bits")

    header = LZW_FILE_ID + struct.pack("<QB", len(data), code_width)

    if not data:
        return header

    dictionary = {bytes([byte]): byte for byte in range(256)}
    next_code = 256
    dictionary_limit = 1 << code_width
    writer = BitWriter()
    current = bytes([data[0]])

    for byte in data[1:]:
        symbol = bytes([byte])
        combined = current + symbol

        if combined in dictionary:
            current = combined
            continue

        writer.write_bits(dictionary[current], code_width)

        if next_code < dictionary_limit:
            dictionary[combined] = next_code
            next_code += 1

        current = symbol

    writer.write_bits(dictionary[current], code_width)
    return header + writer.finish()


def lzw_decompress(encoded):
    if len(encoded) < 13 or encoded[:4] != LZW_FILE_ID:
        raise ValueError("Invalid LZW file header")

    original_size, code_width = struct.unpack("<QB", encoded[4:13])

    if not 9 <= code_width <= 16:
        raise ValueError("Invalid LZW code width")

    if original_size == 0:
        return b""

    dictionary = {byte: bytes([byte]) for byte in range(256)}
    next_code = 256
    dictionary_limit = 1 << code_width
    reader = BitReader(encoded[13:])
    first_code = reader.read_bits(code_width)

    if first_code not in dictionary:
        raise ValueError("Invalid first LZW code")

    previous = dictionary[first_code]
    result = bytearray(previous)

    while len(result) < original_size:
        code = reader.read_bits(code_width)

        if code in dictionary:
            entry = dictionary[code]
        elif code == next_code:
            entry = previous + previous[:1]
        else:
            raise ValueError("Invalid LZW code")

        if len(result) + len(entry) > original_size:
            raise ValueError("LZW data is longer than the original file")

        result.extend(entry)

        if next_code < dictionary_limit:
            dictionary[next_code] = previous + entry[:1]
            next_code += 1

        previous = entry

    return bytes(result)
