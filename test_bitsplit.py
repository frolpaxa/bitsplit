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
    """Key should be masked_data:count:size format (3 parts)."""
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


def test_unique_keys():
    """Files with same header but different content should get different keys."""
    # Simulate two fMP4 chunks: same 17-byte header, different payload
    header = os.urandom(17)
    data1 = header + os.urandom(500)
    data2 = header + os.urandom(500)
    _, key1 = encode(data1)
    _, key2 = encode(data2)
    assert key1 != key2
    # Both should decode correctly
    block1, key1 = encode(data1)
    assert decode(block1, key1) == data1
    block2, key2 = encode(data2)
    assert decode(block2, key2) == data2


def test_legacy_salted_key():
    """Old keys with salt (4 parts) should still decode."""
    data = os.urandom(500)
    block, key = encode(data)
    # Simulate legacy salted key: unmask with block hash, then re-salt with random
    import hashlib
    sample = block[:4096] if len(block) > 4096 else block
    block_hash = int.from_bytes(hashlib.sha256(sample).digest()[:16], "big")
    parts = key.split(":")
    real_key_data = int(parts[0]) ^ block_hash  # unmask to get original key_data
    import secrets
    salt = secrets.randbits(128)
    salted = real_key_data ^ salt
    legacy_key = f"{salted}:{parts[1]}:{parts[2]}:{salt}"
    assert decode(block, legacy_key) == data
