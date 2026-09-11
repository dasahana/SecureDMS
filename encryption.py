from pathlib import Path
from cryptography.fernet import Fernet

# SecureDMS encryption configuration
BASE_DIR = Path(__file__).resolve().parent
KEY_FILE = BASE_DIR / "encryption.key"
ENCRYPTED_FOLDER = BASE_DIR / "secure_storage"


def get_encryption_key():
    """Load the existing Fernet key or create it for a new installation.

    Never replace an existing key when encrypted documents are present.
    """
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()

    if ENCRYPTED_FOLDER.exists() and any(ENCRYPTED_FOLDER.iterdir()):
        raise RuntimeError(
            "encryption.key is missing while encrypted documents exist. "
            "Restore the original key before accessing documents."
        )

    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    return key


def get_fernet():
    return Fernet(get_encryption_key())


def encrypt_file(file_bytes, output_path):
    """Encrypt plaintext bytes and write the encrypted result to output_path."""
    # Accept bytearray/memoryview as well as bytes.
    if isinstance(file_bytes, (bytearray, memoryview)):
        file_bytes = bytes(file_bytes)

    if not isinstance(file_bytes, bytes):
        raise TypeError(
            "encrypt_file() expects plaintext bytes as the first argument."
        )

    # Normalize Path/string only for the output path.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    encrypted = get_fernet().encrypt(file_bytes)
    output_path.write_bytes(encrypted)


def decrypt_file(encrypted_path):
    """Read an encrypted file and return decrypted bytes."""
    encrypted_path = Path(encrypted_path)
    encrypted_bytes = encrypted_path.read_bytes()
    return get_fernet().decrypt(encrypted_bytes)


# Compatibility helpers used by older SecureDMS modules.
def ensure_storage_directory():
    ENCRYPTED_FOLDER.mkdir(parents=True, exist_ok=True)
    return ENCRYPTED_FOLDER


def generate_encryption_key():
    return Fernet.generate_key()


def save_encryption_key(key):
    KEY_FILE.write_bytes(key)


def load_encryption_key():
    return get_encryption_key()


def encrypt_data(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return get_fernet().encrypt(data)


def decrypt_data(data):
    return get_fernet().decrypt(data)


def save_encrypted_data(data, filename):
    path = ENCRYPTED_FOLDER / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def load_encrypted_data(filename):
    return (ENCRYPTED_FOLDER / filename).read_bytes()


def delete_encrypted_file(filename):
    path = ENCRYPTED_FOLDER / filename
    if path.exists():
        path.unlink()


def encryption_key_exists():
    return KEY_FILE.exists()
