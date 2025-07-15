import os
import secrets
from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key

ENV_FILE_PATH = ".env"

# Function to ensure encryption keys exist
def ensure_encryption_keys():
    """Check if API_SECRET_KEY and PASSWORD_SALT exist in .env; if not, generate and store them."""
    api_secret_key = os.getenv("API_SECRET_KEY")
    password_salt = os.getenv("PASSWORD_SALT")

    if not api_secret_key:
        api_secret_key = Fernet.generate_key().decode()
        set_key(ENV_FILE_PATH, "API_SECRET_KEY", api_secret_key)
        print("Generated and stored API_SECRET_KEY.")
    else:
        print("API Secret Key already initialized.")

    if not password_salt:
        password_salt = secrets.token_hex(16)
        set_key(ENV_FILE_PATH, "PASSWORD_SALT", password_salt)
        print("Generated and stored PASSWORD_SALT.")
    else:
        print("Password Salt already initialized.")


if __name__ == "__main__":
    load_dotenv(ENV_FILE_PATH)
    ensure_encryption_keys()