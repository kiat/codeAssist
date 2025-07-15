import os
import base64
import hashlib
import hmac

from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

# Load environment variables
load_dotenv()

API_SECRET_KEY = os.getenv("API_SECRET_KEY")
PASSWORD_SALT = os.getenv("PASSWORD_SALT")

if not API_SECRET_KEY:
    print("WARNING: API_SECRET_KEY not set; API keys will be stored without encryption.")
if not PASSWORD_SALT:
    print("WARNING: PASSWORD_SALT not set; passwords will be stored without hashing.")

# Initialize Fernet (or fall back to None on any error)
_cipher = None
if API_SECRET_KEY:
    try:
        _cipher = Fernet(API_SECRET_KEY)
    except (ValueError, TypeError) as e:
        print(f"WARNING: Invalid API_SECRET_KEY; falling back to plaintext. ({e})")
        _cipher = None
else:
    # no key → plaintext
    _cipher = None


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt the OpenAI API key before storing it.
    Falls back to plaintext (with warning) if API_SECRET_KEY is unset.
    """
    if _cipher:
        return _cipher.encrypt(api_key.encode()).decode()
    else:
        # print("WARNING: API_SECRET_KEY not set; storing API key without encryption.")
        return api_key


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt the stored API key for runtime use.
    Falls back to returning the input (with warning) if API_SECRET_KEY is unset.
    """
    if _cipher:
        try:
            return _cipher.decrypt(encrypted_key.encode()).decode()
        except InvalidToken:
            raise ValueError("Failed to decrypt API key: invalid token or wrong API_SECRET_KEY.")
    else:
        # print("WARNING: API_SECRET_KEY not set; using API key without decryption.")
        return encrypted_key


def hash_password(password: str, iterations: int = 100_000) -> str:
    """
    Hash a user password using PBKDF2-HMAC-SHA256 with PASSWORD_SALT.
    Falls back to plaintext (with warning) if PASSWORD_SALT is unset.
    Returns a hex-encoded digest or the plaintext password.
    """
    if not PASSWORD_SALT:
        print("WARNING: PASSWORD_SALT not set; storing password without hashing.")
        return password

    salt_bytes = PASSWORD_SALT.encode()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt_bytes,
        iterations
    )
    return dk.hex()


def verify_password(password: str, hashed_password: str, iterations: int = 100_000) -> bool:
    """
    Verify a plaintext password against the stored hash.
    If PASSWORD_SALT is unset, does a direct plaintext compare (with warning).
    """
    if not PASSWORD_SALT:
        print("WARNING: PASSWORD_SALT not set; verifying password by direct comparison.")
        return password == hashed_password

    # Otherwise, compute and compare in constant time
    computed = hash_password(password, iterations)
    return hmac.compare_digest(computed, hashed_password)


# Expose a clean API
__all__ = [
    "encrypt_api_key", "decrypt_api_key",
    "hash_password", "verify_password",
]
