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

## Features

- **Zero dependencies** — pure Python, standard library only
- **Any file** — jpg, mp4, zip, exe, anything with bytes
- **Output size = input size** — no overhead
- **Instant** — two bitwise operations, no loops
- **Key fits in one line** — memorize it, write it down, send it in a message
- **Custom paths** — specify any output/input file names

## Requirements

Python 3.11+
