# CLI and Usage Details

This document covers everything you need to actually run the tool — commands, flags,
workflows, and how to handle errors when things go wrong.

> **Project status note:** The CLI dispatch and several core modules are currently in
> progress. The commands below reflect the intended interface. Check the README for current
> module completion status before running.

---

## Supported Image Formats

| Format | Supported | Notes |
|---|---|---|
| PNG | ✅ | Recommended — lossless, compact |
| BMP | ✅ | Lossless, larger file sizes |
| JPEG / JPG | ❌ | Lossy compression destroys hidden data |

Always use PNG or BMP as your carrier image. If you only have a JPEG, convert it to PNG
first — *before* encoding anything into it. See `technical_overview.md` →
[Lossless vs. Lossy Image Formats] for why JPEG is incompatible.

---

## Commands

### Encode a message into an image

```bash
python cli.py encode input.png output.png "Your secret message"
```

### Encode with password protection

```bash
python cli.py encode input.png output.png "Your secret message" --password mypassword
```

The message is encrypted before embedding. The same password is required to decode it.
See `encoding_and_decoding.md` → [Encryption] for how encryption fits into the pipeline.

### Decode a message from an image

```bash
python cli.py decode output.png
```

### Decode a password-protected message

```bash
python cli.py decode output.png --password mypassword
```

---

## Arguments Reference

| Argument | Command | Required | Description |
|---|---|---|---|
| `input.png` | encode | Yes | Path to the original carrier image (PNG or BMP) |
| `output.png` | encode | Yes | Path to save the encoded image |
| `"message"` | encode | Yes | The text to hide |
| `--password` | encode, decode | No | Encrypts/decrypts the message |
| `input.png` | decode | Yes | Path to the image containing the hidden message |

---

## Full Workflow Example

```bash
# Step 1 — check the image has enough room (optional but recommended)
python -c "
from image_utils import load_image
from capacity import calculate_capacity, required_capacity
img = load_image('photo.png')
msg = 'meet at the usual place'.encode('utf-8')
print(f'Available: {calculate_capacity(img)} bits')
print(f'Required:  {required_capacity(msg)} bits')
"

# Step 2 — encode
python cli.py encode photo.png steg_photo.png "meet at the usual place"
# → Message hidden in steg_photo.png

# Step 3 — send steg_photo.png to recipient (exact file, not screenshot)

# Step 4 — recipient decodes
python cli.py decode steg_photo.png
# → meet at the usual place
```

---

## Project Module Structure

Understanding which module is responsible for what helps when you're debugging or
contributing.

```
cli.py
  └── encoder.py / decoder.py      ← orchestrates the pipeline
        ├── capacity.py             ← validates message fits before embedding
        ├── crypto.py               ← encrypts/decrypts if password provided
        ├── lsb.py                  ← reads/writes bits at the pixel level
        └── image_utils.py          ← loads and saves images via Pillow
```

**What each module does:**

- **`cli.py`** — Parses command-line arguments, dispatches to encoder or decoder, catches
  exceptions and prints user-friendly error messages. This is the only layer that should
  ever `print()` to the terminal or call `sys.exit()`.

- **`encoder.py`** — The encoding pipeline orchestrator. Calls `capacity.py`,
  optionally `crypto.py`, then `lsb.py`, then saves the output image. Returns or saves
  the modified image.

- **`decoder.py`** — The decoding pipeline orchestrator. Calls `lsb.py` to extract bits,
  reassembles bytes, optionally calls `crypto.py` to decrypt, returns the message string.

- **`lsb.py`** — Low-level bit operations. `embed_bits()` writes a bitstream into pixel
  LSBs. `extract_bits()` reads them back out. Knows nothing about messages, encryption,
  or file formats.

- **`capacity.py`** — Calculates `width × height × 3` (available bits) and
  `32 + len(message_bytes) × 8` (required bits). Raises `CapacityError` if the message
  is too large.

- **`crypto.py`** — Encrypts bytes before embedding and decrypts bytes after extraction.
  Takes a password, returns bytes. Raises `DecryptionError` on failure.

- **`image_utils.py`** — Loads images via Pillow (`load_image`), provides pixel access
  (`get_pixel`, `set_pixel`), and saves output images. All image I/O goes through here.

- **`exceptions.py`** — Custom exception hierarchy: `StegoError` (base),
  `CapacityError`, `DecryptionError`. Business logic raises these; `cli.py` catches them.

---

## Exception Handling

The CLI catches all custom exceptions and prints readable messages. You should never see
a raw Python traceback from normal usage.

| Exception | Cause | Where it's raised |
|---|---|---|
| `CapacityError` | Message too large for the image | `capacity.py` |
| `DecryptionError` | Wrong password or corrupted ciphertext | `crypto.py` |
| `StegoError` | No message found, corrupted header, invalid length | `decoder.py` |
| `IOError` | Image file not found or unreadable | `image_utils.py` |

---

## Troubleshooting

### "Message too large for image"

The message (after optional encryption) exceeds the image's capacity. Options:
- Use a larger carrier image
- Shorten or compress the message
- Once implemented: use `--bits 2` to double available capacity at a small quality cost

### Decoded message is garbled or unreadable

Most likely causes, in order of probability:

1. **The image was re-saved as JPEG.** JPEG destroys LSBs. Always transmit the exact PNG
   or BMP file.
2. **The image was resized or resampled.** Any operation that averages or interpolates
   pixels corrupts the hidden bits.
3. **Wrong `--password` on decode.** If the message was encoded with a password, the
   exact same password is required to decode it.
4. **Mismatched parameters.** The decoder must use the same bit depth and channel order
   as the encoder.

### "No hidden message found"

- You may be running `decode` on the original image rather than the encoded output.
- The image may have been processed (resized, cropped, screenshot, uploaded to social
  media) after encoding.
- No message was ever embedded in this image.

### Program raises an error on JPEG input

This is intentional. Convert the image to PNG first:

```bash
# Using ImageMagick
convert photo.jpg photo.png

# Then encode into the PNG
python cli.py encode photo.png output.png "your message"
```

### `image_utils.py` crashes when imported

The module currently contains test code that runs at import time (outside a
`if __name__ == "__main__":` guard). This is a known issue — see the TODO comments in
`image_utils.py`. Until fixed, importing the module will attempt to load
`"path/to/image.png"` and fail.

---

## Best Practices

- **Use PNG for output**, even if your input is BMP. PNG is lossless and produces smaller
  files.
- **Don't post encoded images to social media.** Most platforms recompress uploads as
  JPEG, destroying the hidden data.
- **Use `--password` for anything sensitive.** LSB alone is not a secret — anyone who
  knows to look can extract the bits. Encryption ensures they can't read them.
- **Keep your original carrier image.** Don't overwrite it with the encoded version — you
  may want to reuse it or compare the two.
- **Name encoded files inconspicuously.** A filename like `output_steg.png` is an obvious
  giveaway. Use a name that fits the context.
- **Transfer the exact file.** Don't screenshot it, don't re-export from an image editor,
  don't let a messaging app recompress it.

---

## Learning Resources

If you're exploring this project to learn, these resources cover the core concepts:

- [Pillow documentation](https://pillow.readthedocs.io/en/stable/) — image processing in Python
- [Python bitwise operators](https://realpython.com/python-bitwise-operators/) — essential for LSB manipulation
- [Unicode and UTF-8 explained](https://www.joelonsoftware.com/2003/10/08/the-absolute-minimum-every-software-developer-absolutely-positively-must-know-about-unicode-and-character-sets-no-excuses/) — why encoding matters
- [Python argparse tutorial](https://docs.python.org/3/howto/argparse.html) — building CLIs
- [Python custom exceptions](https://realpython.com/python-exceptions/) — clean error handling