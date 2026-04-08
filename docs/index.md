# bitsplit

**Split any file into a keyless binary block and a 128-bit text key.**

```
photo.jpg  -->  data.bin + key.txt
  1.05 MB       1.05 MB    102 B
```

Without the key, the block is useless. The key is a single line of text — memorize it, write it down, or send it in a message.

## Quick start

```bash
pip install bitsplit
```

```bash
# Encode
bitsplit encode secret.pdf

# Decode
bitsplit decode restored.pdf
```

```{toctree}
:maxdepth: 2

how-it-works
cli
api
security
```
