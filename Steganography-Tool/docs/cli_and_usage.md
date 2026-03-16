# CLI and Usage Details

This document covers how to use the tool from the command line.

> **Note:** The CLI dispatch and several core modules are currently in progress. The
> commands below reflect the intended interface. Check the README for current module
> completion status before running.

---

## Supported Image Formats

| Format | Supported |
|---|---|
| PNG | ✅ |
| BMP | ✅ |
| JPEG / JPG | ❌ |

Always use PNG or BMP. JPEG uses lossy compression and will destroy any hidden data.

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

### Decode a message from an image

```bash
python cli.py decode output.png
```

### Decode a password-protected message

```bash
python cli.py decode output.png --password mypassword
```

---

## Arguments

| Argument | Description |
|---|---|
| `input.png` | Path to the original image (PNG or BMP) |
| `output.png` | Path to save the encoded image |
| `"message"` | The text to hide |
| `--password` | Optional. Encrypts the message before embedding |

---

## Project Structure

```
lsb-steganography/
│
├── cli.py           # Command-line interface
├── encoder.py       # Encoding pipeline
├── decoder.py       # Decoding pipeline
├── lsb.py           # Core LSB logic
├── crypto.py        # Optional encryption/decryption
├── capacity.py      # Calculates whether a message fits in an image
├── image_utils.py   # Image loading and saving utilities
├── exceptions.py    # Custom exceptions
└── requirements.txt # Project dependencies
```

### How the modules connect

```
cli.py
  └── encoder.py / decoder.py
        ├── capacity.py
        ├── crypto.py
        ├── lsb.py
        └── image_utils.py
```
