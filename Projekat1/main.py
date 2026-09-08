import sys
from pathlib import Path

import algorithms
import lz

COMPRESSORS = {
    "shannon-fano": algorithms.shannon_fano_compress,
    "huffman": algorithms.huffman_compress,
    "lz77": lz.lz77_compress,
    "lzw": lz.lzw_compress,
}

FILE_ID_TO_DECOMPRESSOR = {
    algorithms.SHANNON_FANO_FILE_ID: algorithms.shannon_fano_decompress,
    algorithms.HUFFMAN_FILE_ID: algorithms.huffman_decompress,
    lz.LZ77_FILE_ID: lz.lz77_decompress,
    lz.LZW_FILE_ID: lz.lzw_decompress,
}

def show_entropy(input_name):
    data = Path(input_name).read_bytes()
    print(f"File: {input_name}")
    print(f"Size: {len(data)} bytes")
    print(f"Byte entropy: {algorithms.byte_entropy(data):.6f} bits/byte")

def compress_file(method, input_name, output_name):
    data = Path(input_name).read_bytes()
    compress = COMPRESSORS[method]
    encoded = compress(data)
    output_path = Path(output_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encoded)
    print(f"Compressed {len(data)} bytes to {len(encoded)} bytes")

def decompress_file(input_name, output_name):
    encoded = Path(input_name).read_bytes()

    if len(encoded) < 4 or encoded[:4] not in FILE_ID_TO_DECOMPRESSOR:
        raise ValueError("Unknown compressed file format")

    decoded = FILE_ID_TO_DECOMPRESSOR[encoded[:4]](encoded)
    output_path = Path(output_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(decoded)
    print(f"Decompressed file has {len(decoded)} bytes")

def main():
    if len(sys.argv) < 2:
        print("Invalid arguments")
        return

    command = sys.argv[1]

    try:
        if command == "entropy" and len(sys.argv) == 3:
            show_entropy(sys.argv[2])
        elif command == "compress" and len(sys.argv) == 5:
            method = sys.argv[2]

            if method not in COMPRESSORS:
                raise ValueError("Unknown compression method")

            compress_file(method, sys.argv[3], sys.argv[4])
        elif command == "decompress" and len(sys.argv) == 4:
            decompress_file(sys.argv[2], sys.argv[3])
        else:
            print("Invalid arguments")
    except (OSError, ValueError) as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()