import os
import base64
import hashlib
import hmac

from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

# Load environment variables
load_dotenv()

API_SECRET_KEY = os.getenv("API_SECRET_KEY")

PASSWORD_SALT = os.getenv("PASSWORD_SALT", "")

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

def pepper() -> bytes:
    if PASSWORD_SALT:
        return PASSWORD_SALT.encode("utf-8")
    else:
        return b""

def hash_password(password: str, iterations: int = 100_000) -> str:
    """
    Hash a user password using PBKDF2-HMAC-SHA256 with PASSWORD_SALT.
    Falls back to plaintext (with warning) if PASSWORD_SALT is unset.
    Returns a hex-encoded digest or the plaintext password.
    """
    # Similar to before, this just helps verify passwords for unit tests
    if not PASSWORD_SALT:
        return password 
    
    salt_bytes = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes + pepper(),
        iterations
    )

    return base64.b64encode(salt_bytes + dk).decode("utf-8")


def verify_password(password: str, hashed_password: str, iterations: int = 100_000) -> bool:
    """
    Verify a plaintext password against the stored hash.
    If PASSWORD_SALT is unset, does a direct plaintext compare (with warning).
    """
    try:
        if not PASSWORD_SALT:
            return hmac.compare_digest(password, hashed_password)

        decoded: base64.b64decode(hashed_password.encode("utf-8"))
        salt = decoded[:16]
        original_hash = decoded[16:]
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt + pepper(),
            iterations
        )
        return hmac.compare_digest(original_hash, candidate)
    
    except Exception as e:
        print(f"Password verification failed: {e}")
        return False


# Expose a clean API
__all__ = [
    "encrypt_api_key", "decrypt_api_key",
    "hash_password", "verify_password",
]
