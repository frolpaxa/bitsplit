"""bitsplit — split any file into a binary block and a 128-bit text key."""

__version__ = "1.0.0"

from .core import decode, decode_file, encode, encode_file

__all__ = ["encode", "decode", "encode_file", "decode_file"]
