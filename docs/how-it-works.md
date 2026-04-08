# How it works

## The idea

Any file is a sequence of bytes. Any sequence of bytes is a number. bitsplit takes that number, slices off the top 128 bits as the **key**, and stores the rest as the **block**.

```
File (bytes)  →  Number  →  [ key: 128 bits | block: the rest ]
                                   |                 |
                                key.txt          data.bin
```

## Step by step

### Encoding

1. Read the file as raw bytes.
2. Convert bytes to a single big integer: `number = int.from_bytes(data, "big")`.
3. Split the integer:
   - `key_data = number >> count` — the top 128 bits.
   - `indices = number & ((1 << count) - 1)` — everything below.
4. Write `indices` as raw bytes to `data.bin`.
5. Write `key_data:count:size` to `key.txt`.

### Decoding

1. Read the key: `key_data`, `count`, `size`.
2. Read the block as `indices`.
3. Reconstruct: `number = (key_data << count) | indices`.
4. Convert back to bytes: `number.to_bytes(size, "big")`.

## Why `size` is stored

When a file starts with zero bytes (e.g., `\x00\x00...`), the leading zeros are lost during `int.from_bytes` → `to_bytes` conversion. Storing the original file size guarantees exact byte-level restoration.

## Diagram

```
Original file:     FF D8 FF E0 00 10 4A 46 49 46 ...
                   ↓
As a number:       110111111101100011111111 ... (very long binary)
                   ├── top 128 bits ──┤── rest ──────────────────┤
                   ↓                  ↓
                key.txt            data.bin
```
