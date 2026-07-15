# Delivery and security considerations

## What bitsplit does

bitsplit changes how a file is delivered. Instead of exposing a ready-to-use
JPEG, MP4, ZIP, or other file at one public URL, a service can expose a binary
block and deliver the reconstruction data through its client flow.

This raises the effort required for direct downloading, hotlinking, and generic
scraping. A downloader may need to discover endpoints, reproduce a session,
collect chunks or byte ranges, restore them, and assemble the final file.

## What bitsplit does not do

bitsplit is not encryption, DRM, or an access-control system. The block contains
most of the original bytes in unencrypted form. A determined downloader who can
observe a legitimate browser can reproduce the reconstruction process.

Separating 128 bits does not establish 128-bit cryptographic security. Known
headers, predictable formats, and partial-data analysis can reveal information
without reconstructing the complete file.

## Appropriate uses

- Preventing a public URL from returning a finished media file
- Making simple “save URL” workflows fail
- Raising the cost of hotlinking and generic media scraping
- Browser-side reconstruction with JavaScript or a Service Worker
- Combining delivery with sessions, authorization, rate limits, and short-lived
  URLs

## Inappropriate uses

- Protecting secrets or personal data
- Compliance or cryptographic confidentiality
- Preventing an authorized viewer from copying content
- Claiming that downloading or reconstruction is impossible

Use an established encryption scheme such as AES or ChaCha20 when disclosure of
the underlying bytes would matter.
