import os
import re
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_SIZE = 16
NONCE_SIZE = 12
PBKDF2_ITERATIONS = 480_000


def check_password_strength(password: str) -> tuple[str, str]:
    """
    Evaluates password strength based on standard security heuristics:
    length, uppercase, lowercase, digits, and special characters.

    Returns:
        tuple[str, str]: (strength_description, hex_color)
    """
    if not password:
        return "", "gray"

    length = len(password)
    has_lower = bool(re.search(r"[a-z]", password))
    has_upper = bool(re.search(r"[A-Z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", password))

    variety_count = sum([has_lower, has_upper, has_digit, has_special])

    if length < 6 or variety_count <= 1:
        return "Strength: Weak (Use 8+ characters with uppercase, numbers, and symbols)", "#d9534f"
    elif length >= 10 and variety_count >= 3:
        return "Strength: Strong (Optimal entropy for PBKDF2 key derivation)", "#2e7d32"
    elif length >= 8 and variety_count >= 2:
        return "Strength: Moderate (Add symbols or numbers for greater security)", "#f0ad4e"
    else:
        return "Strength: Weak (Too short or low character diversity)", "#d9534f"


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