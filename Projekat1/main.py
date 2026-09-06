import argparse
from pathlib import Path

from algorithms import (
    HUFFMAN_FILE_ID,
    SHANNON_FANO_FILE_ID,
    byte_entropy,
    huffman_compress,
    huffman_decompress,
    shannon_fano_compress,
    shannon_fano_decompress,
)
from lz import (
    LZ77_FILE_ID,
    LZW_FILE_ID,
    lz77_compress,
    lz77_decompress,
    lzw_compress,
    lzw_decompress,
)


COMPRESSORS = {
    "shannon-fano": shannon_fano_compress,
    "huffman": huffman_compress,
    "lz77": lz77_compress,
    "lzw": lzw_compress,
}

FILE_ID_TO_DECOMPRESSOR = {
    SHANNON_FANO_FILE_ID: shannon_fano_decompress,
    HUFFMAN_FILE_ID: huffman_decompress,
    LZ77_FILE_ID: lz77_decompress,
    LZW_FILE_ID: lzw_decompress,
}


def show_entropy(input_name):
    data = Path(input_name).read_bytes()
    print(f"File: {input_name}")
    print(f"Size: {len(data)} bytes")
    print(f"Byte entropy: {byte_entropy(data):.6f} bits/byte")


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


def build_parser():
    parser = argparse.ArgumentParser(description="Basic data compression algorithms")
    commands = parser.add_subparsers(dest="command", required=True)

    entropy_parser = commands.add_parser("entropy", help="calculate byte entropy")
    entropy_parser.add_argument("input")

    compress_parser = commands.add_parser("compress", help="compress a file")
    compress_parser.add_argument("method", choices=COMPRESSORS)
    compress_parser.add_argument("input")
    compress_parser.add_argument("output")

    decompress_parser = commands.add_parser("decompress", help="decompress a file")
    decompress_parser.add_argument("input")
    decompress_parser.add_argument("output")

    return parser


def main():
    parser = build_parser()
    arguments = parser.parse_args()

    try:
        if arguments.command == "entropy":
            show_entropy(arguments.input)
        elif arguments.command == "compress":
            compress_file(arguments.method, arguments.input, arguments.output)
        elif arguments.command == "decompress":
            decompress_file(arguments.input, arguments.output)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
