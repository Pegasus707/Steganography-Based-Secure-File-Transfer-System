import struct
import wave
import cv2
import numpy as np
import miniaudio

LENGTH_HEADER_SIZE = 4  # 32-bit uint length header


# ==========================================
# 1. IMAGE STEGANOGRAPHY (PNG, JPG, JPEG)
# ==========================================

def get_image_capacity(image_path: str) -> int:
    """Calculates byte capacity for any supported image format."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not read the selected image file.")
    return (img.size // 8) - LENGTH_HEADER_SIZE


def hide_in_image(carrier_path: str, data: bytes, output_path: str) -> str:
    """
    Embeds encrypted bytes into image pixels.
    Enforces .png output to guarantee lossless persistence.
    """
    img = cv2.imread(carrier_path)
    if img is None:
        raise ValueError("Could not read carrier image.")

    if not output_path.lower().endswith(".png"):
        output_path = output_path.rsplit(".", 1)[0] + ".png"

    max_bytes = (img.size // 8) - LENGTH_HEADER_SIZE
    if len(data) > max_bytes:
        raise ValueError(
            f"Payload ({len(data):,} bytes) exceeds image capacity ({max_bytes:,} bytes)."
        )

    full_payload = struct.pack(">I", len(data)) + data
    bits = np.unpackbits(np.frombuffer(full_payload, dtype=np.uint8))

    flat = img.flatten()
    flat[:len(bits)] = (flat[:len(bits)] & np.uint8(0xFE)) | bits
    stego_img = flat.reshape(img.shape)

    cv2.imwrite(output_path, stego_img)
    return output_path


def extract_from_image(stego_path: str) -> bytes:
    """Extracts hidden bytes from an LSB-encoded image."""
    img = cv2.imread(stego_path)
    if img is None:
        raise ValueError("Could not open stego image.")

    flat = img.flatten()
    if len(flat) < LENGTH_HEADER_SIZE * 8:
        raise ValueError("Image file too small to contain valid metadata.")

    header_bits = flat[:LENGTH_HEADER_SIZE * 8] & 1
    payload_len = struct.unpack(">I", np.packbits(header_bits).tobytes())[0]

    total_bits = (LENGTH_HEADER_SIZE + payload_len) * 8
    if total_bits > len(flat):
        raise ValueError("No valid hidden payload found or image is corrupted.")

    payload_bits = flat[LENGTH_HEADER_SIZE * 8:total_bits] & 1
    return np.packbits(payload_bits).tobytes()


# ==========================================
# 2. AUDIO STEGANOGRAPHY (WAV, MP3)
# ==========================================

def _load_audio_frames(audio_path: str):
    """
    Decodes MP3 (via miniaudio) or reads standard WAV into raw PCM byte frames.
    Returns: (nchannels, sampwidth, framerate, frames_bytearray)
    """
    if audio_path.lower().endswith(".mp3"):
        # Decode MP3 to raw signed 16-bit PCM
        decoded = miniaudio.decode_file(
            audio_path,
            output_format=miniaudio.SampleFormat.SIGNED16
        )
        return (
            decoded.nchannels,
            2,  # 16-bit = 2 bytes per sample
            decoded.sample_rate,
            bytearray(decoded.samples)
        )
    else:
        with wave.open(audio_path, "rb") as song:
            nchannels = song.getnchannels()
            sampwidth = song.getsampwidth()
            framerate = song.getframerate()
            frames = bytearray(song.readframes(song.getnframes()))
            return (nchannels, sampwidth, framerate, frames)


def get_audio_capacity(audio_path: str) -> int:
    """Calculates byte capacity for WAV or MP3 audio files."""
    _, _, _, frames = _load_audio_frames(audio_path)
    return (len(frames) // 8) - LENGTH_HEADER_SIZE


def hide_in_audio(carrier_path: str, data: bytes, output_path: str) -> str:
    """
    Embeds encrypted bytes into audio samples.
    Enforces .wav output to guarantee lossless persistence.
    """
    nchannels, sampwidth, framerate, frames = _load_audio_frames(carrier_path)

    if not output_path.lower().endswith(".wav"):
        output_path = output_path.rsplit(".", 1)[0] + ".wav"

    max_bytes = (len(frames) // 8) - LENGTH_HEADER_SIZE
    if len(data) > max_bytes:
        raise ValueError(
            f"Payload ({len(data):,} bytes) exceeds audio capacity ({max_bytes:,} bytes)."
        )

    full_payload = struct.pack(">I", len(data)) + data
    bits = [(b >> i) & 1 for b in full_payload for i in range(7, -1, -1)]

    for i, bit in enumerate(bits):
        frames[i] = (frames[i] & 0xFE) | bit

    with wave.open(output_path, "wb") as song:
        song.setnchannels(nchannels)
        song.setsampwidth(sampwidth)
        song.setframerate(framerate)
        song.writeframes(bytes(frames))

    return output_path


def extract_from_audio(stego_path: str) -> bytes:
    """Extracts hidden bytes from an LSB-encoded WAV file."""
    with wave.open(stego_path, "rb") as song:
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
        raise ValueError("No hidden payload found or audio file is corrupted.")

    data_bytes = bytearray()
    for i in range(32, total_bits, 8):
        byte = 0
        for b in [frames[j] & 1 for j in range(i, i + 8)]:
            byte = (byte << 1) | b
        data_bytes.append(byte)

    return bytes(data_bytes)