"""Core encode/decode logic."""

import hashlib
import os
import shutil
import sys

sys.set_int_max_str_digits(0)

KEY_BITS = 128
_HEAD_LEN = 17  # bytes needed to extract 128-bit key (16 + 1 for alignment)
_CHUNK = 1 << 20  # 1 MB streaming buffer


# ---------------------------------------------------------------------------
# In-memory API
# ---------------------------------------------------------------------------

def encode(data: bytes) -> tuple[bytes, str]:
    """Encode bytes into a binary block and a key string.

    Args:
        data: Source file content as bytes.

    Returns:
        (block, key) where block is bytes and key is "data:count:size:salt" string.
    """
    size = len(data)

    if size <= 16:
        block, raw_key = _encode_small(data, size)
    elif _first_nz(data, size) + _HEAD_LEN > size:
        block, raw_key = _encode_bigint(data, size)
    else:
        block, raw_key = _encode_main(data, size)

    key = _mask_key(raw_key, block)
    return block, key


def decode(block: bytes, key: str) -> bytes:
    """Decode a binary block using the key string.

    Args:
        block: Binary block (indices).
        key: Key string in "data:count:size" format (masked with block hash)
             or legacy "data:count:size:salt" format.

    Returns:
        Restored file content as bytes.
    """
    key_data, count, size = _parse_key(key, block)

    if size <= 16 or count == 0:
        return _decode_small(key_data, count, size, block)

    total_bits = count + KEY_BITS
    total_bytes = (total_bits + 7) // 8
    nz = size - total_bytes
    fb = total_bits - (total_bytes - 1) * 8

    if not (1 <= fb <= 8) or nz + _HEAD_LEN > size:
        return _decode_bigint(key_data, count, size, block)

    expected_block = total_bytes - 16  # size - nz - 16
    actual_block = len(block)
    missing = expected_block - actual_block

    if missing > 0:
        # Old format: leading zero bytes were stripped
        remainder = 0
        head_int = key_data << fb
        head_bytes = head_int.to_bytes(_HEAD_LEN, "big")
        return b"\x00" * nz + head_bytes + b"\x00" * (missing - 1) + block
    else:
        remainder = block[0]
        head_int = (key_data << fb) | remainder
        head_bytes = head_int.to_bytes(_HEAD_LEN, "big")
        return b"\x00" * nz + head_bytes + block[1:]


# ---------------------------------------------------------------------------
# Streaming file API
# ---------------------------------------------------------------------------

def encode_file(input_path: str, block_path: str, key_path: str) -> int:
    """Encode a file into a block file and a key file (streaming).

    Returns:
        Size of the written block in bytes.
    """
    size = os.path.getsize(input_path)

    if size <= 16:
        data = open(input_path, "rb").read()
        block, raw_key = _encode_small(data, size)
        _write(block_path, block)
        _write_text(key_path, _mask_key(raw_key, block))
        return len(block)

    with open(input_path, "rb") as fin:
        # Find first non-zero byte
        nz = 0
        while nz < size:
            b = fin.read(1)
            if b != b"\x00":
                break
            nz += 1

        if nz + _HEAD_LEN > size:
            # Very sparse — fall back to in-memory
            fin.seek(0)
            data = fin.read()
            block, raw_key = _encode_bigint(data, size)
            _write(block_path, block)
            _write_text(key_path, _mask_key(raw_key, block))
            return len(block)

        # Read head: the first non-zero byte (already read as `b`) + 16 more
        rest_head = fin.read(_HEAD_LEN - 1)
        head = b + rest_head
        fb = head[0].bit_length()
        head_int = int.from_bytes(head, "big")

        total_bits = (size - nz - 1) * 8 + fb
        count = total_bits - KEY_BITS

        key_data = head_int >> fb
        remainder = head_int & ((1 << fb) - 1)

        block_size = 0
        with open(block_path, "wb") as fout:
            fout.write(bytes([remainder]))
            block_size += 1
            # Stream the rest of the file
            shutil.copyfileobj(fin, fout, length=_CHUNK)
            block_size += size - nz - _HEAD_LEN

    raw_key = f"{key_data}:{count}:{size}"
    # Read block sample for hash-based masking
    with open(block_path, "rb") as fb:
        block_sample = fb.read(_HASH_SAMPLE)
    _write_text(key_path, _mask_key(raw_key, block_sample))
    return block_size


def decode_file(block_path: str, key_path: str, output_path: str) -> int:
    """Decode a block file using a key file (streaming).

    Returns:
        Size of the restored file in bytes.
    """
    key_str = open(key_path, "r").read().strip()
    with open(block_path, "rb") as fb:
        block_sample = fb.read(_HASH_SAMPLE)
    key_data, count, size = _parse_key(key_str, block_sample)

    if size <= 16 or count == 0:
        block = open(block_path, "rb").read()
        data = _decode_small(key_data, count, size, block)
        _write(output_path, data)
        return size

    total_bits = count + KEY_BITS
    total_bytes = (total_bits + 7) // 8
    nz = size - total_bytes
    fb = total_bits - (total_bytes - 1) * 8

    if not (1 <= fb <= 8) or nz + _HEAD_LEN > size:
        block = open(block_path, "rb").read()
        data = _decode_bigint(key_data, count, size, block)
        _write(output_path, data)
        return size

    expected_block = total_bytes - 16
    actual_block = os.path.getsize(block_path)
    missing = expected_block - actual_block

    with open(block_path, "rb") as fblock, open(output_path, "wb") as fout:
        if nz > 0:
            fout.write(b"\x00" * nz)

        if missing > 0:
            # Old format: leading zeros were stripped
            head_int = key_data << fb
            head_bytes = head_int.to_bytes(_HEAD_LEN, "big")
            fout.write(head_bytes)
            if missing > 1:
                fout.write(b"\x00" * (missing - 1))
            shutil.copyfileobj(fblock, fout, length=_CHUNK)
        else:
            remainder = fblock.read(1)
            head_int = (key_data << fb) | remainder[0]
            head_bytes = head_int.to_bytes(_HEAD_LEN, "big")
            fout.write(head_bytes)
            shutil.copyfileobj(fblock, fout, length=_CHUNK)

    return size


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _first_nz(data: bytes, size: int) -> int:
    """Return index of first non-zero byte."""
    nz = 0
    while nz < size and data[nz] == 0:
        nz += 1
    return nz


def _encode_main(data: bytes, size: int) -> tuple[bytes, str]:
    """Encode a file using the standard head-extraction algorithm."""
    nz = _first_nz(data, size)
    head = data[nz : nz + _HEAD_LEN]
    fb = head[0].bit_length()
    head_int = int.from_bytes(head, "big")

    total_bits = (size - nz - 1) * 8 + fb
    count = total_bits - KEY_BITS

    key_data = head_int >> fb
    remainder = head_int & ((1 << fb) - 1)

    block = bytes([remainder]) + data[nz + _HEAD_LEN :]
    key = f"{key_data}:{count}:{size}"
    return block, key


_HASH_SAMPLE = 4096  # bytes to hash for key derivation


def _block_hash(block: bytes) -> int:
    """Derive a 128-bit hash from the first bytes of the block."""
    sample = block[:_HASH_SAMPLE] if len(block) > _HASH_SAMPLE else block
    digest = hashlib.sha256(sample).digest()[:16]
    return int.from_bytes(digest, "big")


def _mask_key(raw_key: str, block: bytes) -> str:
    """XOR key_data with block hash to make the key unique.

    Skips masking for empty/tiny blocks (small files, all-zeros, etc.)
    where the block has no meaningful differentiating content.
    """
    parts = raw_key.split(":")
    if len(block) < 2:
        return raw_key
    key_data = int(parts[0])
    masked = key_data ^ _block_hash(block)
    return f"{masked}:{parts[1]}:{parts[2]}"


def _parse_key(key: str, block: bytes = None) -> tuple[int, int, int]:
    """Parse key string, unmasking with block hash if available."""
    parts = key.split(":")
    if len(parts) == 4:
        # Legacy salted format: data:count:size:salt
        salt = int(parts[3])
        key_data = int(parts[0]) ^ salt
    elif block is not None and len(block) > 0:
        # New format: data XORed with block hash
        key_data = int(parts[0]) ^ _block_hash(block)
    else:
        # Raw/legacy format without salt
        key_data = int(parts[0])
    count = int(parts[1])
    size = int(parts[2])
    return key_data, count, size


def _encode_small(data: bytes, size: int) -> tuple[bytes, str]:
    """Encode a small file (≤16 bytes) using big-int."""
    number = int.from_bytes(data, "big")
    bits = number.bit_length()
    if bits > KEY_BITS:
        count = bits - KEY_BITS
        key_data = number >> count
    else:
        count = 0
        key_data = number
    key = f"{key_data}:{count}:{size}"
    return b"", key


def _encode_bigint(data: bytes, size: int) -> tuple[bytes, str]:
    """Fallback: encode using full big-int (for edge cases)."""
    number = int.from_bytes(data, "big")
    bits = number.bit_length()
    if bits > KEY_BITS:
        count = bits - KEY_BITS
        key_data = number >> count
        indices = number & ((1 << count) - 1)
    else:
        count = 0
        key_data = number
        indices = 0
    if indices > 0:
        block = indices.to_bytes((indices.bit_length() + 7) // 8, "big")
    else:
        block = b""
    key = f"{key_data}:{count}:{size}"
    return block, key


def _decode_small(key_data: int, count: int, size: int, block: bytes) -> bytes:
    """Decode a small file or zero-count file."""
    indices = int.from_bytes(block, "big") if block else 0
    number = (key_data << count) | indices
    return number.to_bytes(size, "big")


def _decode_bigint(key_data: int, count: int, size: int, block: bytes) -> bytes:
    """Fallback: decode using full big-int."""
    indices = int.from_bytes(block, "big") if block else 0
    number = (key_data << count) | indices
    return number.to_bytes(size, "big")


def _write(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)


def _write_text(path: str, text: str) -> None:
    with open(path, "w") as f:
        f.write(text)
