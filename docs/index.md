# bitsplit

**Stop serving ready-to-download files.**

```
photo.jpg  -->  data.bin + key.txt
  1.05 MB       1.05 MB    102 B
```

bitsplit turns a file into a binary block and a short text key. Public clients
must obtain both parts and reconstruct the original instead of downloading a
finished file from one URL.

The block is not encrypted and may reveal most of the source bytes. bitsplit is
designed to impede casual downloads, hotlinking, and generic scrapers—not to
provide confidentiality.

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
