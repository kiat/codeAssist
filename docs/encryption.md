# Encryption Docs
This doc goes over the components of the application that handle the secure storage and access of sensitive credentials, such as passwords and API keys.

## Components
`backend/util/encryption_utils.py` provides four functions:

`encrypt_api_key(api_key: str) -> str:` Encrypts API keys with Fernet.

`decrypt_api_key(encrypted_key: str) -> str:` Decrypts stored API keys.

`hash_password(password: str, iterations: int = 100_000) -> str:` Hashes user passwords using PBKDF2-HMAC-SHA256.

`verify_password(password: str, hashed_password: str, iterations: int = 100_000) -> bool:` Verifies a plaintext password against a hash.

These encryption functions automatically load the following environment variables:

`API_SECRET_KEY:` Base64-encoded 32-byte key for Fernet encryption.

`PASSWORD_SALT:` Random salt string for PBKDF2.

If either variable is missing or invalid, the module prints a warning and falls back to plaintext storage/comparison.

> Note: In a production environment, always ensure .env contains both API_SECRET_KEY and PASSWORD_SALT. The fallback plaintext behavior is intended only to prevent hard errors in development or misconfigured environments.

## Setup

1. Ensure a `.env` file is initialized at /backend
2. Run the initializer script: ```python init_encryption_keys.py``` This will populate .env with API_SECRET_KEY and PASSWORD_SALT if they aren’t already set.

> Note: Once the `API_SECRET_KEY` and `PASSWORD_SALT` are initialized, they should be recorded. If the same application, with the same database tables needs to be deployed somewhere else, the same environment variables will need to be copied over to access the data. 