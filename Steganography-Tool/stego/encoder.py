# TODO: Add imports for all modules this function needs to coordinate:
# lsb.py, capacity.py, crypto.py, exceptions.py, and image_utils.py.
# Without these, encode_message cannot fulfill its role as the pipeline orchestrator.

import lsb
import crypto
from exceptions import CapacityError
from image_utils import load_image, save_image


def encode_message(image, message, password=None):
    # TODO: Add type annotations to the signature.
    # What type is `image`? A PIL.Image object? A file path string?
    # This must be consistent with how cli.py calls this function.

    if isinstance(image, str):
        image = load_image(image)   
    


    # TODO: Add step 1 — convert message string to bytes using message.encode('utf-8').
    # Learn about str.encode() and why UTF-8 matters for non-ASCII characters
    # (see recommended resources from earlier analysis).

    message_bytes = message.encode('utf-8')


    # TODO: Add step 2 — if password is not None, call crypto.encrypt_message()
    # before converting to bits. Encryption must happen before bit conversion.
    # The caller (cli.py) should never need to know whether encryption occurred.

    if password is not None:
        message_bytes = crypto.encrypt_message(message_bytes, password)


    # TODO: Add step 3 — perform capacity check using capacity.py BEFORE embedding.
    # Raise CapacityError with a descriptive message if the message is too large.
    # This prevents a silent failure or image corruption.

    capacity = lsb.calculate_capacity(image)
    if len(message_bytes) * 8 + 32 > capacity:
        raise CapacityError(f"Message is too large to embed. Required bits: {len(message_bytes) * 8 + 32}, Available bits: {capacity}")

    # TODO: Add step 4 — prepend the 32-bit length header to the bitstream.
    # The decoder depends on this header to know how many bits to read.
    # Without it, decoding is impossible. See decoding.md for the pipeline spec.

    # TODO: Add step 5 — convert bytes to a flat bitstream and call lsb.embed_bits().
    # Decide here what type your bitstream is (matches your decision in lsb.py).

    # TODO: Decide and document the return value — should this function return the
    # modified image object, or save it to disk itself?
    # Returning the image and letting cli.py save it is better separation of concerns.
    """Convert message to bits and embed into the image."""
    pass