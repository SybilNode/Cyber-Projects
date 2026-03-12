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
    # TODO: Cache the result of img.load() instead of calling it on every get_pixel invocation.
    # Calling img.load() repeatedly is wasteful — it returns a PixelAccess object that should be reused.
    # Learn about Pillow's PixelAccess object (see recommended resources from earlier analysis).
    """Get the RGB values of a pixel at (x, y)."""
    return img.load()[x,y]

def set_pixel(img, x, y, value):
    # TODO: Add validation that `value` is a valid RGB tuple (3 integers each between 0–255).
    # Passing an invalid value causes a cryptic downstream error with no useful message.
    # TODO: Cache the result of img.load() here too — same issue as get_pixel.
    """Set the RGB values of a pixel at (x, y)."""
    img.load()[x,y] = value

# TODO: Add a save_image(img, path) utility function here.
# The encoder needs to save the output image, but there is no utility for it.
# This function should also validate that the path ends in .png or .bmp — never .jpg/.jpeg.

# TODO: CRITICAL — Move all code below this line into an `if __name__ == "__main__":` block.
# This code runs unconditionally at import time, crashing any module that imports from image_utils.
# This is the highest-priority fix in the entire project.
# Learn about the Python module execution model and the __name__ guard
# (see recommended resources from earlier analysis).
img = load_image("path/to/image.png")
print("Width:", img.width)
print("Height:", img.height)
print("Mode:", img.mode)
img.save("test_output.png")

print("Before:", get_pixel(img, 50, 50))
set_pixel(img, 50, 50, (255, 0, 0))  # Set pixel to red
print("After:", get_pixel(img, 50, 50))