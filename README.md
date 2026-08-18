# Steganography-Based Secure File Transfer System

A Python application for securely hiding encrypted data inside image and audio carrier files. The system combines **AES-256-GCM authenticated encryption** with **Least Significant Bit (LSB) steganography** so you can transmit secret messages or files inside innocent-looking media.

---

## Application Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/806b2888-b2f8-4994-884d-67714f58f524" alt="Encode & Hide Interface" width="600" />
  <br>
  <em>Encode & Hide Interface</em>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/3f2dc5e1-56df-448e-a5a6-64ab61e90653" alt="Extract & Decrypt Interface" width="600" />
  <br>
  <em>Extract & Decrypt Interface</em>
</p>

---

## Features

- **AES-256-GCM Encryption**: Encrypts plaintext messages or files with a password before embedding.
- **PBKDF2 Key Derivation**: Uses SHA-256 with 480,000 iterations to derive strong encryption keys from user passwords.
- **Dual Media Support**: Embeds payloads into images (`PNG`, `JPEG`, `JPG`) and audio files (`WAV`, `MP3`).
- **Lossless Persistence**: Automatically outputs stego files in lossless formats (`.png` for images, `.wav` for audio) to prevent data corruption from compression.
- **Real-Time Capacity Check**: Calculates available storage space in selected carrier files before embedding.
- **Simple Graphical Interface**: Multi-tab Tkinter interface for encoding and decoding workflows.

---

## Project Structure

```
Cyber mini Project/
├── main.py              # Application entry point
├── gui.py               # Tkinter desktop interface
├── crypto_engine.py     # AES-256-GCM encryption & PBKDF2 key derivation
├── stego_engine.py      # LSB image and audio steganography engine
├── assets/              # Screenshots and demo media
└── requirements.txt     # Python dependencies
```

---

## Cryptography & Container Layout

### Key Derivation
- **Algorithm**: PBKDF2-HMAC-SHA256
- **Salt**: 16 random bytes (`os.urandom`)
- **Iterations**: 480,000
- **Key Length**: 32 bytes (256-bit)

### Container Structure
The encrypted blob is packed in the following order before being hidden in carrier media:

```
[ 16B Salt ] [ 12B Nonce ] [ 2B Filename Length ] [ Original Filename ] [ Ciphertext ] [ 16B Auth Tag ]
```

---

## Steganography Details

### 1. Image Steganography
- Carrier image bytes are converted to a 1D array.
- A 4-byte header containing payload length is prepended to the data.
- Payload bits replace the lowest bit of each pixel color channel byte.
- Saved as lossless `.png`.

### 2. Audio Steganography
- MP3 files are decoded into raw 16-bit PCM audio samples, while WAV files are parsed directly.
- Payload length header (4 bytes) and data bits replace the lowest bit of each PCM sample byte.
- Saved as lossless `.wav`.

---

## Installation

### Prerequisites
- **Python 3.9+**
- **Tkinter** (pre-installed with Python on Windows/macOS)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pegasus707/Steganography-Based-Secure-File-Transfer-System.git
   cd Steganography-Based-Secure-File-Transfer-System
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

---

## How to Use

### Hide & Encrypt (Encoding)
1. Open the **Encode & Hide** tab.
2. Choose **Image** or **Audio** and browse for a carrier file.
3. Select payload type (**Text Message** or **File**).
4. Enter an encryption password.
5. Click **Encrypt & Embed Data** and save your output file (`.png` or `.wav`).

### Extract & Decrypt (Decoding)
1. Open the **Extract & Decrypt** tab.
2. Select your stego `.png` or `.wav` file.
3. Enter the decryption password used during encoding.
4. Click **Extract & Decrypt** to view text or save the recovered file.

---

## License

Distributed under the MIT License.
