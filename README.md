<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/frolpaxa/bitsplit/main/logo-dark.png"/>
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/frolpaxa/bitsplit/main/logo-light.png"/>
    <img src="https://raw.githubusercontent.com/frolpaxa/bitsplit/main/logo-light.png" alt="bitsplit" width="400"/>
  </picture>
</p>

<p align="center">
  <em>Split any file into a keyless binary block and a 128-bit text key.</em>
</p>

---

Any file becomes two objects: a binary block and a short text key. Without the key, the block is useless.

```
photo.jpg  -->  data.bin + key.txt
  1.05 MB       1.05 MB    102 B
```

## How it works

The file is interpreted as a single large number. The top 128 bits are sliced off to become the key, the rest is saved as a binary block.

```
File (bytes)  -->  Number  -->  [ data: 128 bits | indices: the rest ]
                                      |                  |
                                   key file          data file
```

Recovery is a single bitwise operation: `(data << count) | indices`.

## Install

```bash
pip install bitsplit
```

## Usage

### CLI

```bash
# Encode: file -> block + key
bitsplit encode photo.jpg
bitsplit encode photo.jpg -d photo.dat -k photo.key

# Decode: block + key -> file
bitsplit decode restored.jpg
bitsplit decode restored.jpg -d photo.dat -k photo.key
```

### Python API

```python
from bitsplit import encode, decode

# Encode
block, key = encode(open("photo.jpg", "rb").read())
# block = bytes, key = "340079...:8843264:1105424"

# Decode
content = decode(block, key)
open("restored.jpg", "wb").write(content)
```

## Key format

```
340079864808174098294188674279182237768:8843264:1105424
|                                      |       |
data (128-bit number)                  count   size (bytes)
```

## Why it can't be restored without the key

The key holds 128 bits of data. Brute-forcing 2^128 variants (~3.4 x 10^38) is infeasible — it would take longer than the age of the universe.

## Use cases

- **Split storage** — file on the cloud, key on your device. A breach of one side is useless without the other
- **Two-channel transfer** — send the block via messenger, the key via SMS. Intercepting one channel reveals nothing
- **Offline backups** — data on an external drive, key on paper in a safe
- **Shared access control** — one person holds the key, another holds the block. Both are required to restore the file
- **CI/CD secrets** — block committed to the repo, key stored in environment variables
- **Geo-distribution** — block in one data center, key in another

> [!CAUTION]
> **bitsplit is not encryption.** It does not use ciphers, rounds, or key derivation. It splits raw data into two parts — neither part is useful without the other. Think of it as tearing a document in half rather than locking it in a safe. The 128-bit key makes brute-force infeasible, but there is no authentication, no padding, and no protection against tampering. If you need a cryptographic standard (compliance, audits, signatures), use AES or ChaCha20.

## Performance

bitsplit uses two bitwise operations with no loops, no block processing, and no rounds — just a single shift and OR. Benchmarked on Apple M2 (8 GB RAM):

### Encode

| File size | bitsplit | OpenSSL AES-256 | OpenSSL ChaCha20 | GPG AES-256 | age | 7-Zip AES-256 |
|-----------|----------|-----------------|------------------|-------------|-----|---------------|
| 1 MB      | 0.08 s   | 0.02 s          | **0.00 s**       | 0.29 s      | 0.02 s | 0.14 s    |
| 10 MB     | 0.04 s   | 0.05 s          | 0.03 s           | 0.45 s      | **0.01 s** | 0.53 s |
| 100 MB    | **0.13 s** | 0.64 s        | 0.36 s           | 2.43 s      | 0.15 s | 4.86 s    |
| 1 GB      | **1.45 s** | 5.11 s        | 3.18 s           | 3.58 s      | 1.56 s | 3.16 s    |
| 5 GB      | **15.6 s** | 58.8 s        | 78.6 s           | 148.5 s     | 10.5 s | 372.2 s   |

### Decode

| File size | bitsplit | OpenSSL AES-256 | OpenSSL ChaCha20 | GPG AES-256 | age | 7-Zip AES-256 |
|-----------|----------|-----------------|------------------|-------------|-----|---------------|
| 1 MB      | 0.02 s   | **0.00 s**      | **0.00 s**       | 0.26 s      | **0.00 s** | 0.01 s |
| 10 MB     | 0.04 s   | 0.05 s          | 0.03 s           | 0.32 s      | **0.02 s** | 0.02 s |
| 100 MB    | **0.08 s** | 0.49 s        | 0.34 s           | 1.09 s      | 0.16 s | 0.09 s    |
| 1 GB      | **1.63 s** | 4.71 s        | 4.35 s           | 1.04 s      | 3.85 s | 0.83 s    |
| 5 GB      | **13.6 s** | 91.8 s        | 45.9 s           | 56.1 s      | 11.0 s | 22.0 s    |

### Peak memory

| File size | bitsplit | OpenSSL AES-256 | OpenSSL ChaCha20 | GPG AES-256 | age | 7-Zip AES-256 |
|-----------|----------|-----------------|------------------|-------------|-----|---------------|
| 1 MB      | 14 MB    | 1.5 MB          | 1.5 MB           | 6 MB        | 7 MB  | —          |
| 10 MB     | 18 MB    | 1.5 MB          | 1.5 MB           | 6 MB        | 7 MB  | —          |
| 100 MB    | 20 MB    | 1.5 MB          | 1.5 MB           | 6 MB        | 7 MB  | —          |
| 1 GB      | 24 MB    | 1.5 MB          | 1.5 MB           | 6 MB        | 7 MB  | —          |
| 5 GB      | 21 MB    | 1.5 MB          | 1.5 MB           | 6 MB        | 7 MB  | 1.6 GB    |

> **Bold** = fastest in row. Streaming I/O keeps memory flat at ~20 MB regardless of file size.

All files restored with identical SHA-256 checksums. Pure Python, zero dependencies.

## Features

- **Zero dependencies** — pure Python, standard library only
- **Any file** — jpg, mp4, zip, exe, anything with bytes
- **Output size = input size** — no overhead
- **Instant** — two bitwise operations, no loops
- **Key fits in one line** — memorize it, write it down, send it in a message
- **Custom paths** — specify any output/input file names

## Requirements

Python 3.11+
