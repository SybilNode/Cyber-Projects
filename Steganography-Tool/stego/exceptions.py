class StegoError(Exception):
    """Base class for steganography-related errors."""
    pass


class CapacityError(StegoError):
    """Raised when the message does not fit inside the image."""
    pass


class DecryptionError(StegoError):
    """Raised when password decryption fails."""
    pass
