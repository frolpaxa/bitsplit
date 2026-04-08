# Security considerations

## What bitsplit is

bitsplit is a **file-splitting tool**. It separates a file into two parts — a small key and a large block — such that both are required to reconstruct the original.

## What bitsplit is not

bitsplit is **not encryption**. It does not use ciphers, random IVs, or key derivation functions.

## Key strength

The key contains 128 bits of data extracted from the file. Brute-forcing 2^128 variants (~3.4 × 10^38) is computationally infeasible with current and foreseeable technology.

For reference:

- 2^128 ≈ 3.4 × 10^38
- All computers on Earth doing 10^18 operations/sec would need ~10^13 years
- The universe is ~1.4 × 10^10 years old

## Known properties

### Deterministic

The same file always produces the same key and block. There is no randomness in the process.

### Block is not encrypted

The block (`data.bin`) contains the lower bits of the file interpreted as a number. It is not ciphertext — it is a subset of the original data.

### Format-aware attacks

If an attacker knows the file format (e.g., JPEG starts with `FF D8 FF`), they know some of the top bits, reducing the unknown key space. For JPEG (4-byte known header), the key space reduces from 2^128 to ~2^96 — still infeasible to brute-force.

## Recommendations

- **Keep `key.txt` private.** Anyone with both the key and block can restore the file.
- **Store key and block separately.** The whole point is that neither is useful alone.
- **For sensitive data**, consider using bitsplit in combination with real encryption (e.g., AES-256 via `gpg` or `age`).

## Comparison with encryption

| Property           | bitsplit          | AES-256              |
| ------------------ | ----------------- | -------------------- |
| Key source         | Derived from file | Independent / random |
| Deterministic      | Yes               | No (random IV)       |
| Block looks random | No                | Yes                  |
| Key size           | 128 bits          | 256 bits             |
| Speed              | Instant           | Fast                 |
| Dependencies       | None              | Crypto library       |
