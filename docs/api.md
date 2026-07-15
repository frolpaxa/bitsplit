# Python API

## Quick example

```python
from bitsplit import encode, decode

# Encode any bytes
data = open("photo.jpg", "rb").read()
block, key = encode(data)

# block is bytes (the binary block)
# key is a string like "340079...:8843264:1105424"

# Decode back
restored = decode(block, key)
assert restored == data
```

## Functions

```{eval-rst}
.. automodule:: bitsplit.core
   :members:
   :undoc-members:
```

## Key string format

The key returned by `encode()` is a colon-separated string:

```
<data>:<count>:<size>
```

| Field | Type | Description |
|-------|------|-------------|
| `data` | `int` | Top 128 bits of the file as a number |
| `count` | `int` | Number of lower bits stored in the block |
| `size` | `int` | Original file size in bytes |

## Constants

```{eval-rst}
.. autodata:: bitsplit.core.KEY_BITS
```

`KEY_BITS = 128` — the number of bits separated into the reconstruction key.
This is a format parameter, not a cryptographic security level.
