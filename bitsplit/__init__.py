"""bitsplit — stop serving ready-to-download files."""

__version__ = "2.0.1"

from .core import decode, decode_file, encode, encode_file

__all__ = ["encode", "decode", "encode_file", "decode_file"]
