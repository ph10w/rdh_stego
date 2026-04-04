from PIL import Image
import numpy as np
import struct
import os
import hashlib
import shutil

HEADER_PIXELS = 2000
STRUCT_FORMAT = "<BBIHH"  # peak, zero, payload_len, filename_len, hash_len
HASH_LEN = 32  # SHA-256 = 32 Bytes

# -------------------------
# Bit-Helper
# -------------------------
def to_bits(data: bytes):
    return ''.join(format(b, '08b') for b in data)

def from_bits(bits: str):
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

# -------------------------
# LSB Header
# -------------------------
def embed_header_lsb(flat, header_bytes):
    bits = to_bits(header_bytes)
    flat = flat.copy()
    for i in range(len(bits)):
        flat[i] = (flat[i] & 0xFE) | int(bits[i])
    return flat

def extract_header_lsb(flat, num_bytes):
    bits = ""
    for i in range(num_bytes * 8):
        bits += str(flat[i] & 1)
    return from_bits(bits)

# -------------------------
# Histogram Shifting Embed/Extract
# -------------------------
def hs_embed(flat, bits, peak, zero, start_idx):
    flat = flat.copy()
    region = flat[start_idx:]
    # Shift
    if zero > peak:
        mask = (region > peak) & (region < zero)
        region[mask] += 1
    else:
        mask = (region < peak) & (region > zero)
        region[mask] -= 1
    bit_idx = 0
    for i in range(len(region)):
        if region[i] == peak and bit_idx < len(bits):
            if bits[bit_idx] == '1':
                region[i] += 1 if zero > peak else -1
            bit_idx += 1
    flat[start_idx:] = region
    return flat

def hs_extract(flat, peak, zero, bit_length, start_idx):
    region = flat[start_idx:].copy()
    bits = ""
    for i in range(len(region)):
        if region[i] == peak:
            bits += '0'
        elif region[i] == peak + 1 and zero > peak:
            bits += '1'
            region[i] = peak
        elif region[i] == peak - 1 and zero < peak:
            bits += '1'
            region[i] = peak
        if len(bits) >= bit_length:
            break
    # Restore
    if zero > peak:
        mask = (region > peak) & (region <= zero)
        region[mask] -= 1
    else:
        mask = (region < peak) & (region >= zero)
        region[mask] += 1
    flat_restored = flat.copy()
    flat_restored[start_idx:] = region
    return bits, flat_restored

# -------------------------
# EMBED FILE (mit Hash)
# -------------------------
def embed_file(image_path, output_path, file_path):
    img = Image.open(image_path).convert("L")
    arr = np.array(img)
    flat = arr.flatten()
    if len(flat) < HEADER_PIXELS:
        raise Exception("Bild zu klein")

    # Datei laden
    with open(file_path, "rb") as f:
        file_data = f.read()

    filename_bytes = os.path.basename(file_path).encode()
    sha256_hash = hashlib.sha256(file_data).digest()  # 32 Bytes
    payload = filename_bytes + file_data + sha256_hash

    # Histogram ohne Header
    data_region = flat[HEADER_PIXELS:]
    hist = np.bincount(data_region, minlength=256)
    peak = int(np.argmax(hist))
    zero = next(i for i in range(256) if hist[i] == 0)

    payload_bits = to_bits(payload)
    capacity = np.sum(data_region == peak)
    if len(payload_bits) > capacity:
        raise Exception(f"Nicht genug Kapazität! {capacity} Bits verfügbar")

    # Header bauen
    header = struct.pack(
        STRUCT_FORMAT,
        peak,
        zero,
        len(payload),
        len(filename_bytes),
        HASH_LEN
    )

    # Embed
    flat2 = hs_embed(flat, payload_bits, peak, zero, HEADER_PIXELS)
    flat3 = embed_header_lsb(flat2, header)

    stego = flat3.reshape(arr.shape)
    Image.fromarray(stego.astype(np.uint8)).save(output_path)
    print(f"✅ Embed erfolgreich: {os.path.basename(file_path)} ({len(payload_bits)} Bits)")

# -------------------------
# EXTRACT FILE (mit Hash)
# -------------------------
def extract_file(stego_path, output_folder):
    img = Image.open(stego_path).convert("L")
    arr = np.array(img)
    flat = arr.flatten()

    header_size = struct.calcsize(STRUCT_FORMAT)
    header = extract_header_lsb(flat, header_size)
    peak, zero, payload_len, filename_len, hash_len = struct.unpack(STRUCT_FORMAT, header)

    expected_bits = payload_len * 8
    bits, restored_flat = hs_extract(flat, peak, zero, expected_bits, HEADER_PIXELS)
    payload = from_bits(bits)

    filename = payload[:filename_len].decode()
    file_data = payload[filename_len:-hash_len]
    hash_extracted = payload[-hash_len:]
    
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)
    with open(output_path, "wb") as f:
        f.write(file_data)

    sha_check = hashlib.sha256(file_data).digest()
    if sha_check == hash_extracted:
        print(f"✅ Integrität OK: {filename}")
    else:
        print(f"❌ Integritätsprüfung fehlgeschlagen: {filename}")

    restored_img = Image.fromarray(restored_flat.reshape(arr.shape).astype(np.uint8))
    return output_path, restored_img

# -------------------------
# update_file_in_stego
# -------------------------
def update_file_in_stego(stego_path, new_file_path, output_path, temp_output_folder="./temp"):
    """
    Aktualisiert oder fügt eine Datei in einem Stego-Bild hinzu.
    - Erkennt, ob das Bild gültige RDH-Daten enthält.
    - Falls ungültig oder beschädigt, wird das Bild wie neu behandelt.
    """

    os.makedirs(temp_output_folder, exist_ok=True)

    img = Image.open(stego_path).convert("L")
    arr = np.array(img)
    flat = arr.flatten()

    header_size = struct.calcsize(STRUCT_FORMAT)
    header_valid = False

    try:
        # Header auslesen
        header_bytes = extract_header_lsb(flat, header_size)
        peak, zero, payload_len, filename_len, hash_len = struct.unpack(STRUCT_FORMAT, header_bytes)

        # Prüfe Payload-Länge und Filename-Länge auf sinnvolle Werte
        if payload_len > 0 and filename_len > 0 and filename_len < payload_len:
            # Payload auslesen
            expected_bits = payload_len * 8
            bits, _ = hs_extract(flat, peak, zero, expected_bits, HEADER_PIXELS)
            payload = from_bits(bits)

            # Dateiname prüfen
            try:
                _ = payload[:filename_len].decode("utf-8")
                header_valid = True
            except UnicodeDecodeError:
                header_valid = False
        else:
            header_valid = False

    except Exception:
        header_valid = False

    if not header_valid:
        print("⚠️ Kein gültiger RDH-Header gefunden – Bild wird wie neu behandelt")
        embed_file(stego_path, output_path, new_file_path)
        if os.path.exists(temp_output_folder):
            shutil.rmtree(temp_output_folder, ignore_errors=True)
        return

    # Header gültig → extract → restore → embed neue Datei
    _, restored_img = extract_file(stego_path, temp_output_folder)
    temp_image_path = os.path.join(temp_output_folder, "restored.png")
    restored_img.save(temp_image_path)
    embed_file(temp_image_path, output_path, new_file_path)

    if os.path.exists(temp_output_folder):
        shutil.rmtree(temp_output_folder, ignore_errors=True)

    print(f"✅ Stego-Bild aktualisiert: {output_path}")