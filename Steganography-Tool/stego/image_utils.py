from PIL import Image

"""
To load and save images using the Pillow library in Python, you use the Image.open() function and the Image.save() method, respectively. 
"""

def load_image(image_path, convert_to_rgb=True):
    """Load an image from the specified path."""
    try:
        img = Image.open(image_path)
        return img.convert('RGB') if convert_to_rgb else img
    except Exception as e:
        raise IOError(f"Error loading image: {e}")
    
def get_pixel(img, x, y):
    # 1. Load image once
    with Image.open(image_path) as img:

        # 2. Cache the pixel map (load() returns a PixelAccess object) and reuse it for all get_pixel calls.
        pixel_map = img.load()
        width, height = img.size

        # 3. Use 'pixels' throughout the loops
        for y in range(height):
            for x in range(width):
                r, g, b = pixel_map[x, y]
                # Process the pixel as needed

    """Get the RGB values of a pixel at (x, y)."""
    return img.load()[x,y]

def set_pixel(img, x, y, value):
    # Set Rgh values of a pixel at (x, y) to the provided value.

    # 1. Validate that value is a tuple of three integers in the range 0-255. If not, raise a ValueError with a descriptive message.
    if not (isinstance(value, tuple) and len(value) == 3):
            raise ValueError("Pixel value must be a tuple of three integers (R, G, B).")

    if not all(isinstance(v, int) and 0 <= v <= 255 for v in value):
        raise ValueError("Each component of the pixel value must be an integer in the range 0-255.")
    
    # 2. Mode check: Ensure the image is in RGB mode before setting a pixel. If not, raise a ValueError with a descriptive message.
    if img.mode != 'RGB':
        raise ValueError(f"Image mode must be 'RGB' to set pixel values. Current mode: {img.mode}")
    
    #3. Cache the pixel map (img.load()) at the start of the function and reuse it for all set_pixel calls. This is a significant performance improvement, especially when setting many pixels in a loop.
    pixels = img.load()  # Cache the pixel map
    pixels[x, y] = tuple(value)  # Use the cached pixel map to set the pixel value

 
    # TODO: Cache the result of img.load() here too — same issue as get_pixel.
    """Set the RGB values of a pixel at (x, y)."""
    img.load()[x,y] = value


def save_image(img, path):
# This function should also validate that the path ends in .png or .bmp — never .jpg/.jpeg.

    """Save the image to the specified path."""
    if not path.lower().endswith(('.png', '.bmp')):
        raise ValueError("Output image must be in PNG or BMP format.")
    try:
        img.save(path)
    except Exception as e:
        raise IOError(f"Error saving image: {e}")

if __name__ == "__main__":

    img = load_image("path/to/image.png")
    print("Width:", img.width)
    print("Height:", img.height)
    print("Mode:", img.mode)
    img.save("test_output.png")

    print("Before:", get_pixel(img, 50, 50))
    set_pixel(img, 50, 50, (255, 0, 0))  # Set pixel to red
    print("After:", get_pixel(img, 50, 50))