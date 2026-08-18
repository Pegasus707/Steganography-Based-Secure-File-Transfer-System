import os
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_SIZE = 16
NONCE_SIZE = 12
PBKDF2_ITERATIONS = 480_000


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_payload(data: bytes, filename: str, password: str) -> bytes:
    """
    Encrypts filename metadata + raw data with AES-256-GCM.
    Structure: [16B Salt] + [12B Nonce] + [Ciphertext + Tag]
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    filename_bytes = filename.encode("utf-8")
    fn_len = len(filename_bytes)
    if fn_len > 65535:
        raise ValueError("Filename is too long.")

    inner_payload = struct.pack(">H", fn_len) + filename_bytes + data
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, inner_payload, None)

    return salt + nonce + ciphertext


def decrypt_payload(blob: bytes, password: str) -> tuple[str, bytes]:
    """
    Decrypts the blob and returns (original_filename, raw_data).
    """
    if len(blob) < SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("Corrupted or incomplete encrypted container.")

    salt = blob[:SALT_SIZE]
    nonce = blob[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = blob[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        raise ValueError("Decryption failed. Wrong password or altered carrier.")

    if len(decrypted) < 2:
        raise ValueError("Corrupted metadata inside decrypted container.")

    fn_len = struct.unpack(">H", decrypted[:2])[0]
    filename = decrypted[2:2 + fn_len].decode("utf-8", errors="replace")
    raw_data = decrypted[2 + fn_len:]

    return filename, raw_data