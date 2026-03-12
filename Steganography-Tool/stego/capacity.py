def calculate_capacity(image):
    """Calculate the maximum number of bits that can be hidden in the image."""
    width, height = image.size
    # Assuming we are using 1 bit per color channel (R, G, B)
    return width * height * 3  # 3 channels (R, G, B)

def required_capacity(message_bytes):
    """Calculate the number of bits required to hide the message."""
    return 32 + len(message_bytes) * 8  # Each byte is 8 bits

if __name__ == "__main__":
    from image_utils import load_image
    
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