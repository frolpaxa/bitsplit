"""Command-line interface for bitsplit."""

import argparse
import sys

from .core import decode, encode


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
        with open(args.input, "rb") as f:
            raw = f.read()

        block, key_str = encode(raw)

        with open(args.data, "wb") as f:
            f.write(block)
        with open(args.key, "w") as f:
            f.write(key_str)

        print(f"Block: {args.data} ({len(block)} bytes)")
        print(f"Key:   {args.key}")

    elif args.command == "decode":
        with open(args.key, "r") as f:
            key_str = f.read()
        with open(args.data, "rb") as f:
            block = f.read()

        content = decode(block, key_str)

        with open(args.output, "wb") as f:
            f.write(content)

        print(f"Restored: {args.output} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
