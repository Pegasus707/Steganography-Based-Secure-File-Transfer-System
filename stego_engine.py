import struct
import wave
import cv2
import numpy as np

LENGTH_HEADER_SIZE = 4  # 32-bit uint length header


# --- IMAGE PROCESSING (OpenCV) ---

def get_image_capacity(image_path: str) -> int:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not open image file.")
    return (img.size // 8) - LENGTH_HEADER_SIZE


def hide_in_image(image_path: str, data: bytes, output_path: str) -> None:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not open carrier image.")

    max_bytes = (img.size // 8) - LENGTH_HEADER_SIZE
    if len(data) > max_bytes:
        raise ValueError(f"Payload ({len(data):,} B) exceeds image capacity ({max_bytes:,} B).")

    full_payload = struct.pack(">I", len(data)) + data
    bits = np.unpackbits(np.frombuffer(full_payload, dtype=np.uint8))

    flat = img.flatten()
    # Use 0xFE (254) instead of ~1 to prevent uint8 negative integer overflow
    flat[:len(bits)] = (flat[:len(bits)] & np.uint8(0xFE)) | bits
    stego_img = flat.reshape(img.shape)

    cv2.imwrite(output_path, stego_img)


def extract_from_image(image_path: str) -> bytes:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not open stego image.")

    flat = img.flatten()
    if len(flat) < LENGTH_HEADER_SIZE * 8:
        raise ValueError("Image file is too small to contain valid metadata.")

    header_bits = flat[:LENGTH_HEADER_SIZE * 8] & 1
    payload_len = struct.unpack(">I", np.packbits(header_bits).tobytes())[0]

    total_bits = (LENGTH_HEADER_SIZE + payload_len) * 8
    if total_bits > len(flat):
        raise ValueError("No hidden data found or image file is corrupted.")

    payload_bits = flat[LENGTH_HEADER_SIZE * 8:total_bits] & 1
    return np.packbits(payload_bits).tobytes()


# --- AUDIO PROCESSING (WAV) ---

def get_audio_capacity(audio_path: str) -> int:
    with wave.open(audio_path, "rb") as song:
        frames = song.getnframes() * song.getnchannels()
        return (frames // 8) - LENGTH_HEADER_SIZE


def hide_in_audio(audio_path: str, data: bytes, output_path: str) -> None:
    with wave.open(audio_path, "rb") as song:
        params = song.getparams()
        frames = bytearray(song.readframes(song.getnframes()))

    max_bytes = (len(frames) // 8) - LENGTH_HEADER_SIZE
    if len(data) > max_bytes:
        raise ValueError(f"Payload ({len(data):,} B) exceeds audio capacity ({max_bytes:,} B).")

    full_payload = struct.pack(">I", len(data)) + data
    bits = [(b >> i) & 1 for b in full_payload for i in range(7, -1, -1)]

    for i, bit in enumerate(bits):
        frames[i] = (frames[i] & 0xFE) | bit

    with wave.open(output_path, "wb") as song:
        song.setparams(params)
        song.writeframes(bytes(frames))


def extract_from_audio(audio_path: str) -> bytes:
    with wave.open(audio_path, "rb") as song:
        frames = bytearray(song.readframes(song.getnframes()))

    if len(frames) < LENGTH_HEADER_SIZE * 8:
        raise ValueError("Audio file too small to contain valid payload.")

    header_bits = [frames[i] & 1 for i in range(32)]
    hdr_bytes = bytearray()
    for i in range(0, 32, 8):
        byte = 0
        for b in header_bits[i:i + 8]:
            byte = (byte << 1) | b
        hdr_bytes.append(byte)

    payload_len = struct.unpack(">I", bytes(hdr_bytes))[0]
    total_bits = (LENGTH_HEADER_SIZE + payload_len) * 8

    if total_bits > len(frames):
        raise ValueError("No hidden data found or audio file is corrupted.")

    data_bytes = bytearray()
    for i in range(32, total_bits, 8):
        byte = 0
        for b in [frames[j] & 1 for j in range(i, i + 8)]:
            byte = (byte << 1) | b
        data_bytes.append(byte)

    return bytes(data_bytes)