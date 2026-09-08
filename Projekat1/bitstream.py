class BitWriter:
    def __init__(self):
        self.data = bytearray()
        self.current_byte = 0
        self.bit_count = 0

    def write_bit(self, bit):
        self.current_byte = (self.current_byte << 1) | bit
        self.bit_count += 1

        if self.bit_count == 8:
            self.data.append(self.current_byte)
            self.current_byte = 0
            self.bit_count = 0

    def write_bits(self, value, count):
        for position in range(count - 1, -1, -1):
            self.write_bit((value >> position) & 1)

    def write_code(self, code):
        for bit in code:
            self.write_bit(int(bit))

    def finish(self):
        if self.bit_count > 0:
            self.current_byte <<= 8 - self.bit_count
            self.data.append(self.current_byte)

        return bytes(self.data)

class BitReader:
    def __init__(self, data):
        self.data = data
        self.byte_position = 0
        self.bit_position = 0

    def read_bit(self):
        if self.byte_position >= len(self.data):
            raise ValueError("Unexpected end of compressed data")

        byte = self.data[self.byte_position]
        bit = (byte >> (7 - self.bit_position)) & 1
        self.bit_position += 1

        if self.bit_position == 8:
            self.byte_position += 1
            self.bit_position = 0

        return bit

    def read_bits(self, count):
        value = 0

        for _ in range(count):
            value = (value << 1) | self.read_bit()

        return value