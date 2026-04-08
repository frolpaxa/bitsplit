"""bitsplit — split any file into a binary block and a 128-bit text key."""

__version__ = "0.1.0"

from .core import decode, encode

__all__ = ["encode", "decode"]
