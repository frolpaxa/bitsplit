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
    """Key should be salted_data:count:size:salt format."""
    block, key = encode(os.urandom(500))
    parts = key.split(":")
    assert len(parts) == 4
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
    fake_key = f"{fake_data}:{parts[1]}:{parts[2]}:{parts[3]}"

    result = decode(block, fake_key)
    assert result != original


def test_api_types():
    """Encode returns (bytes, str), decode returns bytes."""
    block, key = encode(b"test")
    assert isinstance(block, bytes)
    assert isinstance(key, str)
    assert isinstance(decode(block, key), bytes)


def test_unique_keys():
    """Encoding the same data twice should produce different keys."""
    data = os.urandom(500)
    _, key1 = encode(data)
    _, key2 = encode(data)
    assert key1 != key2
    # But both should decode correctly
    block, key1 = encode(data)
    assert decode(block, key1) == data
    block, key2 = encode(data)
    assert decode(block, key2) == data


def test_legacy_key_format():
    """Old keys without salt should still decode."""
    data = b"Hello, bitsplit!"
    block, key = encode(data)
    # Simulate legacy key by stripping salt and using raw key_data
    parts = key.split(":")
    salt = int(parts[3])
    key_data = int(parts[0]) ^ salt
    legacy_key = f"{key_data}:{parts[1]}:{parts[2]}"
    assert decode(block, legacy_key) == data
