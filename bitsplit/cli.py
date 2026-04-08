"""Command-line interface for bitsplit."""

import argparse
import os
import sys

from .core import decode_file, encode_file


def main():
    parser = argparse.ArgumentParser(
        prog="bitsplit",
        description="Split any file into a binary block and a 128-bit text key.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Encode
    enc = sub.add_parser("encode", help="Encode a file into block + key")
    enc.add_argument("input", help="Source file path")
    enc.add_argument(
        "-d", "--data", default="data.bin", help="Output block path (default: data.bin)"
    )
    enc.add_argument(
        "-k", "--key", default="key.txt", help="Output key path (default: key.txt)"
    )

    # Decode
    dec = sub.add_parser("decode", help="Decode a file from block + key")
    dec.add_argument("output", help="Restored file path")
    dec.add_argument(
        "-d", "--data", default="data.bin", help="Input block path (default: data.bin)"
    )
    dec.add_argument(
        "-k", "--key", default="key.txt", help="Input key path (default: key.txt)"
    )

    args = parser.parse_args()

    if args.command == "encode":
        block_size = encode_file(args.input, args.data, args.key)
        print(f"Block: {args.data} ({block_size} bytes)")
        print(f"Key:   {args.key}")

    elif args.command == "decode":
        size = decode_file(args.data, args.key, args.output)
        print(f"Restored: {args.output} ({size} bytes)")


if __name__ == "__main__":
    main()
