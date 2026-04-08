"""Tests for bitsplit encode/decode."""

import os

from bitsplit import decode, encode


def roundtrip(content: bytes) -> bytes:
    """Encode and decode content, return the result."""
    block, key = encode(content)
    return decode(block, key)


def test_single_byte():
    for b in [b"\x00", b"\x01", b"\x7f", b"\xff"]:
        assert roundtrip(b) == b


def test_empty_like():
    assert roundtrip(b"\x00\x00\x00") == b"\x00\x00\x00"


def test_small_data():
    data = b"Hello, bitsplit!"
    assert roundtrip(data) == data


def test_binary_data():
    data = bytes(range(256))
    assert roundtrip(data) == data


def test_random_data():
    data = os.urandom(10_000)
    assert roundtrip(data) == data


def test_large_file():
    data = os.urandom(100_000)
    assert roundtrip(data) == data


def test_all_zeros():
    data = b"\x00" * 1000
    assert roundtrip(data) == data


def test_all_ones():
    data = b"\xff" * 1000
    assert roundtrip(data) == data


def test_key_format():
    """Key should be data:count:size format."""
    block, key = encode(os.urandom(500))
    parts = key.split(":")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)
    assert int(parts[2]) == 500


def test_block_size():
    """Block should be roughly the same size as the input."""
    data = os.urandom(10_000)
    block, _ = encode(data)
    assert abs(len(data) - len(block)) < 20


def test_wrong_key_fails():
    """Decoding with a wrong key should produce different content."""
    original = os.urandom(1000)
    block, key = encode(original)

    parts = key.split(":")
    fake_data = int(parts[0]) ^ 1  # flip one bit
    fake_key = f"{fake_data}:{parts[1]}:{parts[2]}"

    result = decode(block, fake_key)
    assert result != original


def test_api_types():
    """Encode returns (bytes, str), decode returns bytes."""
    block, key = encode(b"test")
    assert isinstance(block, bytes)
    assert isinstance(key, str)
    assert isinstance(decode(block, key), bytes)
