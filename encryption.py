from pathlib import Path
import os
from cryptography.fernet import Fernet

try:
    import streamlit as st
except ImportError:
    st = None

BASE_DIR = Path(__file__).resolve().parent
KEY_FILE = BASE_DIR / "encryption.key"
ENCRYPTED_FOLDER = BASE_DIR / "secure_storage"


def get_encryption_key():
    # Streamlit Cloud secret
    cloud_key = None
    if st is not None:
        try:
            cloud_key = st.secrets.get("ENCRYPTION_KEY")
        except Exception:
            cloud_key = None

    # Optional environment variable fallback
    if not cloud_key:
        cloud_key = os.getenv("ENCRYPTION_KEY")

    if cloud_key:
        if isinstance(cloud_key, str):
            cloud_key = cloud_key.strip().encode("utf-8")
        try:
            Fernet(cloud_key)
        except Exception as error:
            raise RuntimeError(
                f"ENCRYPTION_KEY in Streamlit Secrets is invalid: {error}"
            )
        return cloud_key

    # Local development
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes().strip()
        try:
            Fernet(key)
        except Exception as error:
            raise RuntimeError(f"Local encryption.key is invalid: {error}")
        return key

    # New local installation only
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
    if isinstance(file_bytes, (bytearray, memoryview)):
        file_bytes = bytes(file_bytes)
    if not isinstance(file_bytes, bytes):
        raise TypeError("encrypt_file() expects plaintext bytes as the first argument.")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(get_fernet().encrypt(file_bytes))


def decrypt_file(encrypted_path):
    encrypted_path = Path(encrypted_path)
    return get_fernet().decrypt(encrypted_path.read_bytes())


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
    try:
        return bool(
            (st is not None and st.secrets.get("ENCRYPTION_KEY"))
            or os.getenv("ENCRYPTION_KEY")
            or KEY_FILE.exists()
        )
    except Exception:
        return bool(os.getenv("ENCRYPTION_KEY") or KEY_FILE.exists())
