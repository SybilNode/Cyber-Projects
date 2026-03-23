def calculate_capacity(image):
    """Calculate the maximum number of bits that can be hidden in the image."""
    width, height = image.size
    # Assuming we are using 1 bit per color channel (R, G, B)
    return width * height * 3  # 3 channels (R, G, B)

def required_capacity(message_bytes):
    # TODO: Update the docstring to explicitly require `message_bytes` to be a bytes
    # object (not a str). Consider adding an assertion to enforce this at runtime.
    # This prevents incorrect capacity calculations caused by UTF‑8 multi‑byte
    # characters, where len(string) != len(string.encode('utf-8')).

    if not isinstance(message_bytes, bytes):
        raise TypeError("message_bytes must be a bytes object")


    """Calculate the number of bits required to hide the message."""
    return 32 + len(message_bytes) * 8  # Each byte is 8 bits

    # TODO: Implement a `check_fits(image, message_bytes)` helper that wraps
    # `calculate_capacity` and `required_capacity`. It should raise CapacityError
    # (from exceptions.py) when the message exceeds available capacity. This keeps
    # encoder.py cleaner by centralizing the size‑checking logic.



if __name__ == "__main__":
    from image_utils import load_image
    
    # TODO: Replace "path/to/image.png" with an actual test image before running
    # this script, or add a note explaining that this placeholder path will cause
    # load_image() to fail until updated.

    img = load_image("path/to/image.png")
    capacity = calculate_capacity(img)
    print(f"Image Capacity: {capacity} bits")
    
    message = "Hello, World!"
    message_bytes = message.encode('utf-8')
    required_bits = required_capacity(message_bytes)
    print(f"Required Capacity for message: {required_bits} bits")
    
    if required_bits > capacity:
        print("Warning: The message is too large to fit in the image!")
    else:
        print("The message can be hidden in the image.")